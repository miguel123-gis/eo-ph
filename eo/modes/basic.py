import time
from pathlib import Path
import numpy as np
from eo.base_image import BaseImage
from eo.base_image_collection import BaseImageCollection
from eo.annotated_image import AnnotatedImage
from eo.logger import logger
from eo.image_utils import get_best_image, get_best_images, get_bbox_from_point, search_catalog
from eo.utils import load_config
from eo.constants import REQUIRED_PARAMETERS

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent # eo-ph/
CONFIG = load_config(PROJECT_DIR / 'config.yaml')
log = logger(PROJECT_DIR / 'logs/eo.log')

DTYPE_MAP = {
    'uint8': np.uint8,
    'uint16': np.uint16,
    'float32': np.float32,
}

PROCESSED_IMG_DIR = CONFIG['processed_images_directory']
BANDS_SELECTION = CONFIG['bands']
PH_BDRYS = CONFIG['ph_boundaries_gpkg']
FIGSIZE = CONFIG['figure_size']
DPI = CONFIG['dpi']

class BasicMode:
    def __init__(self, parameters):
        self.parameters = parameters

        self.image_selection = None
        if self.image_selection is None:
            self.image_selection = self._image_selection()

    def _image_selection(self):
        return search_catalog(
            BaseImageCollection(
                start_date = self.parameters.get('start_date'),
                end_date = self.parameters.get('end_date'),
                lon = self.parameters.get('longitude'),
                lat = self.parameters.get('latitude'),
                collection = 'sentinel-2-l2a'
            )
        )

    def check_parameters(self):
        if not all([rp in self.parameters for rp in REQUIRED_PARAMETERS]):
            raise KeyError('Input parameters is incomplete')
        
    def run(self):
        self.check_parameters()
        start_time = time.time()

        if len(self.image_selection) == 0:
            log.error('ZERO IMAGES FOUND BASED ON PAYLOAD')
            raise ValueError('ZERO IMAGES FOUND BASED ON PAYLOAD')
        
        latitude = self.parameters.get('latitude')
        longitude = self.parameters.get('longitude')
        buffer = float(self.parameters.get('buffer'))
        frequency = self.parameters.get('frequency')
        annotate = self.parameters.get('annotate')
        boundary = self.parameters.get('boundary')
        all = self.parameters.get('all')
        to_zip = self.parameters.get('to_zip')
        assets = {**BANDS_SELECTION, 'true_color': 'visual'}
        bbox = get_bbox_from_point(longitude, latitude, 4326, 32651, buffer*1000)
        
        log.info(f'PAYLOAD: {self.parameters}')
        log.info(f'GOT {len(self.image_selection)} IMAGES TO SELECT FROM')

        if frequency:
            log.info('RUNNING IN MULTI MODE')
            best_images = get_best_images(self.image_selection, frequency=frequency)
        else:
            log.info('RUNNING IN SINGLE MODE')
            best_images = [get_best_image(self.image_selection)] # Put in list to be compatible with logic downstream


        for image in best_images:
            if buffer > 0:
                log.info(f'ONLY GETTING AREA {buffer} METERS FROM XY')
                base_img = BaseImage( # TODO Insantiate once/before the loop
                        image_item=image, 
                        band_nums=BANDS_SELECTION, 
                        subset=True, 
                        assets=assets, 
                        bbox=bbox
                    )
            else:
                log.info(f'GETTING ENTIRE IMAGE INTERSECTING XY')
                base_img = BaseImage(image_item=image, band_nums=BANDS_SELECTION, true_color=True) 
                
            if annotate:
                log.info('INCLUDING MAP ANNOTATIONS E.G. CAPTURE DATE, CLOUD COVER, ETC.')

                if boundary:
                    log.info('PLOTTING BOUNDARIES IN EXPORTS')
                    
                annt_img = AnnotatedImage(base_image=base_img)
                annt_img.annotate(
                    boundaries=PH_BDRYS, out_dir=PROCESSED_IMG_DIR, 
                    lon=longitude, lat=latitude,
                    plot_bdry=boundary,
                    figsize=FIGSIZE, dpi=DPI
                )   
            else:
                if all:
                    log.info('GETTING THE RED, GREEN, BLUE AND TRUE-COLOR IMAGES')
                    out_file = base_img.export(export_rgb=True, out_dir=PROCESSED_IMG_DIR, to_zip=to_zip)
                else:
                    out_file = base_img.export(out_dir=PROCESSED_IMG_DIR, to_zip=to_zip)
        end_time = time.time()

        log.info(f'OUT FILE: {out_file}')
        log.info(f"FINISHED IN {round(end_time-start_time, 2)} SECONDS")

        return out_file