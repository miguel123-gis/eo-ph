import yaml
import time
import rasterio
import numpy as np
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

    def _remove_cloud(self, scl_arr: DataArray, rgb_arr: DataArray):
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

        for image in best_images:
            if buffer > 0:
                log.info(f'ONLY GETTING AREA {buffer} METERS FROM XY')
                base_img = BaseImage( # TODO Instantiate once/before the loop
                        image_item=image, 
                        band_list=self.available_bands, 
                        bbox=self.bbox
                    )
            else: # TODO Add max buffer range
                log.info(f'GETTING ENTIRE IMAGE INTERSECTING XY')
                base_img = BaseImage(image_item=image, band_nums=self.available_bands) # TODO Convert to stateless class
            
            # Get SCL asset
            clipped_scl = self._upscale_and_clip(
                raster=base_img.image_item.assets['SCL'].to_dict()['href'],
                upscale_factor=UPSCALE_FACTOR
            )

            # Get visual asset
            with rasterio.open(base_img.image_item.assets['visual'].to_dict()['href']) as src:
                clipped_visual, clipped_profile = self._clip(src, self.bbox)

            to_xarray = lambda arr: DataArray(arr, dims=('band', 'y', 'x')).astype(np.uint8)
            
            # Increase resolution of SCL to 10x10m
            no_clouds = self._remove_cloud(
                scl_arr=to_xarray(clipped_scl),
                rgb_arr=to_xarray(clipped_visual)
            )

            # Replace true_color object then export
            base_img.true_color = no_clouds
            out_file = base_img.export(out_dir=PROCESSED_IMG_DIR, to_zip=to_zip, runtime=start_time_readable)

        end_time = time.time()
        log.info(f'OUT FILE: {out_file}')
        log.info(f"FINISHED IN {round(end_time-start_time, 2)} SECONDS")

        return out_file