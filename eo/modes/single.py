import numpy as np
from pathlib import Path
from eo.base_image import BaseImage
from eo.image_utils import get_best_image, get_bbox_from_point
from eo.utils import load_config

CONFIG = load_config('config.yaml')

DTYPE_MAP = {
    'uint8': np.uint8,
    'uint16': np.uint16,
    'float32': np.float32,
}

LONGITUDE = float(CONFIG['longitude'])
LATITUDE = float(CONFIG['latitude'])
PROCESSED_IMG_DIR = 'data/processed'
BANDS_SELECTION = CONFIG['bands']
BUFFER_SIZE_M = CONFIG['buffer_size_meters']
LOWER_PERC = CONFIG['lower_percentile']
UPPER_PERC = CONFIG['upper_percentile']
NO_DATA_VAL = CONFIG['no_data_value']
MAX_VAL = CONFIG['maximum_value']
BIT_DEPTH = DTYPE_MAP.get(CONFIG['bit_depth'])
GAMMA_CORRECTION = CONFIG['gamma_correction']
CHUNK_SIZE = CONFIG['chunk_size']
EXPORT_RGB = CONFIG['export_rgb']

def run(**kwargs):
    image_selection = kwargs.get('image_selection')
    typ = kwargs.get('typ')
    assets = {**BANDS_SELECTION, 'true_color': 'visual'}
    bbox = get_bbox_from_point(LONGITUDE, LATITUDE, 4326, 32651, BUFFER_SIZE_M)
    best_image = get_best_image(image_selection)

    if typ == 'clip':
        base_img = BaseImage(
                image_item=best_image, 
                band_nums=BANDS_SELECTION, 
                subset=True, 
                assets=assets, 
                bbox=bbox
            )
        
    else:
        base_img = BaseImage(image_item=base_img, band_nums=BANDS_SELECTION, true_color=True)

    base_img.export(export_rgb=EXPORT_RGB, out_dir=PROCESSED_IMG_DIR)
