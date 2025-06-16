import numpy as np
from pathlib import Path
from eo.base_image import BaseImage
from eo.annotated_image import AnnotatedImage
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
PROCESSED_IMG_DIR = CONFIG['processed_images_directory']
PH_BDRYS = CONFIG['ph_boundaries_gpkg']
FIGSIZE = CONFIG['figure_size']
DPI = CONFIG['dpi']
BANDS_SELECTION = CONFIG['bands']
BUFFER_SIZE_M = CONFIG['buffer_size_meters']
LOWER_PERC = CONFIG['lower_percentile']
UPPER_PERC = CONFIG['upper_percentile']
NO_DATA_VAL = CONFIG['no_data_value']
MAX_VAL = CONFIG['maximum_value']
BIT_DEPTH = DTYPE_MAP.get(CONFIG['bit_depth'])
GAMMA_CORRECTION = CONFIG['gamma_correction']
CHUNK_SIZE = CONFIG['chunk_size']

def run(**kwargs):
    image_selection = kwargs.get('image_selection')
    clip = kwargs.get('clip')
    annotate = kwargs.get('annt')
    export_all = kwargs.get('all')
    assets = {**BANDS_SELECTION, 'true_color': 'visual'}
    bbox = get_bbox_from_point(LONGITUDE, LATITUDE, 4326, 32651, BUFFER_SIZE_M*1000)
    best_image = get_best_image(image_selection)

    if clip:
        base_img = BaseImage(
                image_item=best_image, 
                band_nums=BANDS_SELECTION, 
                subset=True, 
                assets=assets, 
                bbox=bbox
            )
    else:
        base_img = BaseImage(image_item=base_img, band_nums=BANDS_SELECTION, true_color=True)
        
    if annotate:
        annt_img = AnnotatedImage(base_image=base_img)
        annt_img.annotate(
            boundaries=PH_BDRYS, out_dir=PROCESSED_IMG_DIR, 
            lon=LONGITUDE, lat=LATITUDE,
            figsize=FIGSIZE, dpi=DPI
        )
    else:
        if export_all:
            base_img.export(export_rgb=True, out_dir=PROCESSED_IMG_DIR)
        else:
            base_img.export(out_dir=PROCESSED_IMG_DIR)
