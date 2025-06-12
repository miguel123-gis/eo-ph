import numpy as np
from pathlib import Path
from eo.base_image import BaseImage
from eo.image_utils import get_best_image, get_bbox_from_point, export
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
SLICE = slice(CONFIG['slice_start'], CONFIG['slice_end'])
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
    bbox = get_bbox_from_point(LONGITUDE, LATITUDE, 4326, 32651, 10*1000)
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

    out_file =  f"{PROCESSED_IMG_DIR}/{base_img.image_item.id}.tif"

    if EXPORT_RGB:
        xarrays = {**base_img.bands, 'true_color': base_img.true_color}
        for name, xarr in xarrays.items():
            band_out_file = out_file.replace('.tif', f'_{name}.tif')
            if not Path(out_file).is_file():
                export(xarr, band_out_file)

    else:
        if not Path(out_file).is_file():
            export(base_img.true_color, out_file)
