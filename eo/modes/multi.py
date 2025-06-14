import numpy as np
from pathlib import Path
from eo.base_image import BaseImage
from eo.image_utils import get_best_images, get_bbox_from_point
from eo.utils import load_config

CONFIG = load_config('config.yaml')

DTYPE_MAP = {
    'uint8': np.uint8,
    'uint16': np.uint16,
    'float32': np.float32,
}

LONGITUDE = float(CONFIG['longitude'])
LATITUDE = float(CONFIG['latitude'])
BUFFER_SIZE_M = CONFIG['buffer_size_meters']
PROCESSED_IMG_DIR = 'data/processed'
BANDS_SELECTION = CONFIG['bands']
LOWER_PERC = CONFIG['lower_percentile']
UPPER_PERC = CONFIG['upper_percentile']
NO_DATA_VAL = CONFIG['no_data_value']
EXPORT_RGB = CONFIG['export_rgb']

def run(**kwargs):
    image_selection = kwargs.get('image_selection')
    typ = kwargs.get('typ')
    assets = {**BANDS_SELECTION, 'true_color': 'visual'}
    bbox = get_bbox_from_point(LONGITUDE, LATITUDE, 4326, 32651, BUFFER_SIZE_M*1000)
    best_images = get_best_images (image_selection, interval='yearly')

    for image in best_images:
        if typ == 'clip':
            base_img = BaseImage(
                image_item=image, 
                band_nums=BANDS_SELECTION, 
                subset=True, 
                assets=assets, 
                bbox=bbox
            )

        else:
            base_img = BaseImage(image_item=image, band_nums=BANDS_SELECTION, true_color=True)

        base_img.export(export_rgb=EXPORT_RGB, out_dir=PROCESSED_IMG_DIR)