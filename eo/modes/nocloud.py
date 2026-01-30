import yaml
import time
import rasterio
import numpy as np
import xarray as xr
from pathlib import Path
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
from xarray import where

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
    def _clip(raster, bbox) -> np.ndarray:
        with rasterio.open(raster) as src:
            window = from_bounds(*bbox.bounds, transform=src.transform)
            src.profile.update({
                'height': window.height,
                'width': window.width,
                'transform': src.window_transform(window)
            })
            
            return xr.DataArray(
                src.read(window=window),
                dims=("band", "y", "x"),
                attrs={
                    "transform": src.window_transform(window),
                    "crs": src.crs.to_string() if src.crs else None,
                    "nodata": src.nodata
                }
            ).rio.write_crs(src.crs.to_string())
        
    @staticmethod
    def _upscale_and_clip(raster, bbox, upscale_factor) -> np.ndarray:
        with rasterio.open(raster) as src:
            window = from_bounds(*bbox.bounds, transform=src.transform)
            out_height = int(window.height * upscale_factor)
            out_width = int(window.width * upscale_factor)
            out_shape = (src.count, out_height, out_width)

            clipped_and_upscaled = src.read(
                window=window,
                out_shape=out_shape,
                resampling=Resampling.bilinear
            )

            new_res = tuple(map(lambda x: x/upscale_factor, src.res))
            new_transform = src.window_transform(window) * src.window_transform(window).scale(
                window.width/out_width,
                window.height/out_height
            )

            return xr.DataArray(
                clipped_and_upscaled,
                dims=("band", "y", "x"),
                attrs={
                    "transform": new_transform,
                    "crs": src.crs.to_string() if src.crs else None,
                    "res": new_res,
                    "nodata": src.nodata
                }
            ).rio.write_crs(src.crs.to_string())
    
    @staticmethod
    def _remove_cloud(scl_arr: xr.DataArray, rgb_arr: xr.DataArray):
    # TODO Make sure both are reshaped like band, y, x
        scl_mask = scl_arr.where(np.isin(scl_arr, [0, 1, 2, 4, 5, 6]), other=100).astype(np.uint8) # Replace cloud pixels with 100
        not_cloud = scl_mask != 100 # Use SCL mask to set values in visual to 0 across all bands
        not_cloud_3d = np.repeat(not_cloud, 3, 0).transpose('band', 'y', 'x').to_numpy() # Convert is_cloud mask from 2d to 3d with 3 channels
        rgb_nocloud = where(not_cloud_3d, rgb_arr, 0) # Replace pixels with 0 in visual
        return rgb_nocloud


    # TODO Override run()
    def run(self):
        self.check_parameters()
        start_time = time.time()

        if len(self.image_selection) == 0:
            log.error('ZERO IMAGES FOUND BASED ON PAYLOAD')
            raise ValueError('ZERO IMAGES FOUND BASED ON PAYLOAD')
        
        frequency = self.parameters.get('frequency')
        
        log.info(f'PAYLOAD: {self.parameters}')
        log.info(f'GOT {len(self.image_selection)} IMAGES TO SELECT FROM')

        if frequency: # Get image ID per month/quarter/etc
            log.info('RUNNING IN MULTI MODE')
            best_images = get_best_images(self.image_selection, frequency=frequency)
            log.info(f"BEST IMAGES: {len(best_images)}")
        else: # Get single image ID
            log.info('RUNNING IN SINGLE MODE')
            best_images = [get_best_image(self.image_selection)] # Put in list to be compatible with logic downstream

        # Compile the images here
        rasters = {
            image.datetime.strftime("%Y%m%d"): {
                'id': image.id,
                'visual': image.assets.get('visual').href,
                'scl': image.assets.get('SCL').href
            }
            for image in best_images
        }
        log.info(f"RASTERS: {len(rasters.keys())}")
        order = sorted(list(rasters.keys()), reverse=True)
        latest_raster = rasters.get(order[0])
        log.info(f"GOT {len(order)} RASTERS: {', '.join(order)}")

        # Remove the cloud pixels in latest image
        latest_vis_arr = self._clip(latest_raster.get('visual'), self.bbox)
        latest_scl_arr = self._upscale_and_clip(latest_raster.get('scl'), self.bbox, upscale_factor=2)
        latest_vis_nc = self._remove_cloud(latest_scl_arr, latest_vis_arr) # Target raster
        for_replacement = latest_vis_nc == 0

        # Start of pixel replacement from previous images
        # At first pass, replaced is same as the target raster. 
        replaced = latest_vis_nc

        for key in order[1:]:
            log.info(f"PROCESSING {key}")
            vis = self._clip(rasters.get(key).get('visual'), self.bbox).astype(np.uint8)
            scl = self._upscale_and_clip(rasters.get(key).get('scl'), self.bbox, upscale_factor=2).astype(np.uint8)
            no_clouds = self._remove_cloud(scl, vis) # For this current period, remove the cloud pixels
            
            # At first pass, the latest raster's cloud pixel is replaced by the next raster.
            # Then, in subsequent passes, pixels that were replaced already will not be replaced.
            replaced = no_clouds.where(
                (replaced == 0) & (for_replacement == True),
                replaced,
            )

            for_replacement = replaced == 0 # If not replaced, then still 0 -> still True/for replacement
        
        # At this point, the latest TIF has all its cloud pixels replaced
        out_file = f"{PROCESSED_IMG_DIR}/{latest_raster.get('id')}_cloudreplaced.tif"
        replaced.rio.write_crs('EPSG:32651')
        replaced.rio.write_transform(latest_vis_arr.attrs['transform'], inplace=True)
        replaced.rio.to_raster(out_file)
        
        end_time = time.time()
        log.info(f'OUT FILE: {out_file}')
        log.info(f"FINISHED IN {round(end_time-start_time, 2)} SECONDS")

        return Path(out_file).resolve()