import numpy as np
from eo.base_image import BaseImage
from eo.image_utils import get_best_images, get_individual_bands, get_visual_asset
from eo.utils import load_config

CONFIG = load_config('config.yaml')

DTYPE_MAP = {
    'uint8': np.uint8,
    'uint16': np.uint16,
    'float32': np.float32,
}

PROCESSED_IMG_DIR = 'data/processed'
BANDS_SELECTION = CONFIG['bands']
SLICE = slice(CONFIG['slice_start'], CONFIG['slice_end'])
LOWER_PERC = CONFIG['lower_percentile']
UPPER_PERC = CONFIG['upper_percentile']
NO_DATA_VAL = CONFIG['no_data_value']

def run(**kwargs):
    image_selection = kwargs.get('image_selection')
    best_images = get_best_images(image_selection, interval='yearly')
    processed_images = {}

    for image in best_images:
        true_color = get_visual_asset(image, subset=SLICE)
        base_img = BaseImage(bands=None, true_color=true_color, lower=LOWER_PERC, upper=UPPER_PERC, no_data_value=NO_DATA_VAL)

        processed_images[image.id] = base_img

    for name, processed_image in processed_images.items():
        processed_image.get_true_color(export=f"{PROCESSED_IMG_DIR}/{name}.tif")