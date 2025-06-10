import numpy as np
from eo.base_image import BaseImage
from eo.image_utils import get_best_image, get_individual_bands, get_visual_asset
from eo.utils import load_config

config = load_config('config.yaml')

DTYPE_MAP = {
    'uint8': np.uint8,
    'uint16': np.uint16,
    'float32': np.float32,
}

PROCESSED_IMG_DIR = 'data/processed'
BANDS_SELECTION = config['bands']
START_DATE = config['start_date']
END_DATE = config['end_date']
LONGITUDE = float(config['longitude'])
LATITUDE = float(config['latitude'])
SLICE = slice(config['slice_start'], config['slice_end'])
LOWER_PERC = config['lower_percentile']
UPPER_PERC = config['upper_percentile']
NO_DATA_VAL = config['no_data_value']
MAX_VAL = config['maximum_value']
BIT_DEPTH = DTYPE_MAP.get(config['bit_depth'])
GAMMA_CORRECTION = config['gamma_correction']
CHUNK_SIZE = config['chunk_size']

def run(**kwargs):
    out_file = kwargs.get('out_file')
    image_selection = kwargs.get('image_selection')

    best_image = get_best_image(image_selection)
    rgb_bands = get_individual_bands(best_image, BANDS_SELECTION, subset=SLICE)
    true_color = get_visual_asset(best_image, subset=SLICE)

    image = (
        BaseImage(bands=rgb_bands, true_color=true_color, lower=LOWER_PERC, upper=UPPER_PERC, no_data_value=NO_DATA_VAL)
        .plot_histogram_with_percentiles()
        .stretch_contrast()
        .stack_bands(['red', 'green', 'blue'])
        .process_stack(max_val=MAX_VAL, gamma=GAMMA_CORRECTION, type=BIT_DEPTH, chunk=CHUNK_SIZE)
    )

    image.get_rgb_stack(export=out_file)