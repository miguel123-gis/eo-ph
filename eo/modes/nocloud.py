import yaml
import time
import rasterio
import numpy as np
import xarray as xr
from shapely.geometry import polygon
from datetime import datetime
from pathlib import Path
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
from rasterio import MemoryFile
from xarray import DataArray, where

from eo.base_image import BaseImage
from eo.annotated_image import AnnotatedImage
from eo.logger import logger
from eo.image_utils import get_bbox_from_point, get_best_images, get_best_image
from .basic import BasicMode
from .. import PROJECT_DIR

with open(Path(PROJECT_DIR / 'data/config.yaml'), "r") as f:
    CONFIG = yaml.safe_load(f)

log = logger(PROJECT_DIR / 'logs/eo.log')

PROCESSED_IMG_DIR = CONFIG['processed_images_directory']
PH_BDRYS = CONFIG['ph_boundaries_gpkg']
FIGSIZE = CONFIG['figure_size']
DPI = CONFIG['dpi']
S2A = CONFIG['collections']['s2a']
UPSCALE_FACTOR = 2 # Increase the resolution by 2 times e.g. 20m x 20m to 10m x 10m
SCL_NONCLOUD = [
    0,  # Missing data
    1,  # Saturated/defective pixel
    2,  # Topographic casted shadows
    4,  # Vegetation
    5,  # Not-vegetated
    6   # Water
]

class NoCloudMode(BasicMode):
    def  __init__(self, parameters):
        super().__init__(parameters)
        self.bbox = get_bbox_from_point(
            float(parameters['longitude']), 
            float(parameters['latitude']), 
            4326, 
            32651, 
            float(parameters['buffer'])*1000
        )

    @staticmethod
    def _clip(active_raster: rasterio.DatasetReader, bbox:polygon.Polygon):
        profile = active_raster.profile
        window = from_bounds(*bbox.bounds, transform=active_raster.transform)
        win_transform = active_raster.window_transform(window)
                    
        profile.update({
            'height': window.height,
            'width': window.width,
            'transform': win_transform
        })
        
        return active_raster.read(window=window), profile


    def _upscale_and_clip(self, raster, upscale_factor) -> np.ndarray:
        with rasterio.open(raster) as src:
            hires = src.read(
                out_shape=(
                    src.count,
                    int(src.height * upscale_factor),
                    int(src.width * upscale_factor)
                ),
                resampling=Resampling.bilinear
            )

            transform = src.transform * src.transform.scale(
                (src.width / hires.shape[-1]),
                (src.height / hires.shape[-2])
            )

            profile = {
                'driver': 'GTiff',
                'dtype': hires.dtype.name,
                'count': 1,
                'width': hires.shape[2],
                'height': hires.shape[1],
                'crs': src.crs,
                'transform': transform,
            }

            # Put in a temporary file
            with MemoryFile() as memfile:
                with memfile.open(**profile) as temp_ds_w:
                    temp_ds_w.write(hires[0], 1) # Writes per band

                with memfile.open() as temp_ds_r:
                    return self._clip(temp_ds_r, self.bbox)[0]
    
    def _replace_cloud(self, target_scl_arr: DataArray, target_rgb_arr: DataArray, source_rgb_arr: DataArray):
        scl_mask = target_scl_arr.where(np.isin(target_scl_arr, [0, 1, 2, 4, 5, 6]), other=100).astype(np.uint8) # Replace cloud pixels with 100
        not_cloud = scl_mask != 100 # Use SCL mask to set values in visual to 0 across all bands
        not_cloud_3d = np.repeat(not_cloud, 3, 0).transpose('band', 'y', 'x').to_numpy() # Convert is_cloud mask from 2d to 3d with 3 channels
        rgb_nocloud = where(not_cloud_3d, target_rgb_arr, 0) # Replace pixels with 0 in visual
        is_cloud = target_rgb_arr == 0
        return where(is_cloud, source_rgb_arr, target_rgb_arr)

    # TODO Override run()
    def run(self):
        self.check_parameters()
        start_time = time.time()
        start_time_readable = datetime.fromtimestamp(start_time).strftime("%Y%m%d_%H%M%S")

        if len(self.image_selection) == 0:
            log.error('ZERO IMAGES FOUND BASED ON PAYLOAD')
            raise ValueError('ZERO IMAGES FOUND BASED ON PAYLOAD')
        
        buffer = float(self.parameters.get('buffer'))
        frequency = self.parameters.get('frequency')
        to_zip = self.parameters.get('to_zip')
        
        log.info(f'PAYLOAD: {self.parameters}')
        log.info(f'GOT {len(self.image_selection)} IMAGES TO SELECT FROM')

        if frequency: # Get image ID per month/quarter/etc
            log.info('RUNNING IN MULTI MODE')
            best_images = get_best_images(self.image_selection, frequency=frequency)
        else: # Get single image ID
            log.info('RUNNING IN SINGLE MODE')
            best_images = [get_best_image(self.image_selection)] # Put in list to be compatible with logic downstream

        # Compile the images here
        rasters = {
            image.datetime.strftime("%Y%m%d"): {
                'visual': image.assets.get('visual').href,
                'scl': image.assets.get('SCL').href
            }
            for image in best_images
        }
        order = sorted(list(rasters.keys()), reverse=True)
        latest_raster = rasters.get(order[0])

        # Remove the cloud pixels in latest image
        latest_vis_arr = xr.open_dataarray(rasters.get(order[0]).get('visual')).astype(np.uint8)
        latest_scl_arr = self._upscale_and_clip(latest_raster.get('scl'), UPSCALE_FACTOR)
        previous_vis_arr = xr.open_dataarray(rasters.get(order[1]).get('visual'))
        latest_vis_replaced = self._replace_cloud(
            latest_scl_arr,
            latest_vis_arr,
            previous_vis_arr, 
        )

        # Start of pixel replacement from previous images
        # At first pass, replaced is same as the target raster. 
        replaced = latest_vis_replaced

        for key in order[1:]:
            vis = xr.open_dataarray(rasters.get(key).get('visual')).astype(np.uint8)
            scl = self._upscale_and_clip(rasters.get(key).get('scl'), UPSCALE_FACTOR).astype(np.uint8)
            no_clouds = self.latest_vis_replaced(scl, vis) # For this current period, remove the cloud pixels
            
            # At first pass, the latest raster's cloud pixel is replaced by the next raster.
            # Then, in subsequent passes, pixels that were replaced already will not be replaced.
            replaced = xr.where(
                (replaced == 0) & (for_replacement == True),
                no_clouds,
                replaced
            )

            for_replacement = replaced == 0 # If not replaced, then still 0 -> still True/for replacement
        
        # At this point, the latest TIF has all its cloud pixels replaced
        out_file = f'{PROCESSED_IMG_DIR}/{latest_raster}_cloudreplaced.tif'
        replaced.rio.to_raster(out_file)
        end_time = time.time()
        log.info(f'OUT FILE: {out_file}')
        log.info(f"FINISHED IN {round(end_time-start_time, 2)} SECONDS")

        return out_file