import numpy as np
from pathlib import Path
from eo.base_image import BaseImage
from eo.annotated_image import AnnotatedImage
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
PROCESSED_IMG_DIR = CONFIG['processed_images_directory']
PH_BDRYS = CONFIG['ph_boundaries_gpkg']
FIGSIZE = CONFIG['figure_size']
DPI = CONFIG['dpi']
BANDS_SELECTION = CONFIG['bands']
LOWER_PERC = CONFIG['lower_percentile']
UPPER_PERC = CONFIG['upper_percentile']
NO_DATA_VAL = CONFIG['no_data_value']

def run(**kwargs):
    image_selection = kwargs.get('image_selection')
    frequency = kwargs.get('freq')
    clip = kwargs.get('clip')
    annotate = kwargs.get('annt')
    export_all = kwargs.get('all')
    plot_boundary = kwargs.get('bdry')
    assets = {**BANDS_SELECTION, 'true_color': 'visual'}
    bbox = get_bbox_from_point(LONGITUDE, LATITUDE, 4326, 32651, BUFFER_SIZE_M*1000)
    best_images = get_best_images(image_selection, frequency=frequency)

    for image in best_images:
        if clip:
            base_img = BaseImage(
                image_item=image, 
                band_nums=BANDS_SELECTION, 
                subset=True, 
                assets=assets, 
                bbox=bbox
            )
        else:
            base_img = BaseImage(image_item=image, band_nums=BANDS_SELECTION, true_color=True)
        if annotate:
            annt_img = AnnotatedImage(base_image=base_img)
            annt_img.annotate(
                boundaries=PH_BDRYS, out_dir=PROCESSED_IMG_DIR, 
                lon=LONGITUDE, lat=LATITUDE,
                plot_bdry=plot_boundary,
                figsize=FIGSIZE, dpi=DPI
            )
        else:
            if export_all:
                base_img.export(export_rgb=True, out_dir=PROCESSED_IMG_DIR)
            else:
                base_img.export(out_dir=PROCESSED_IMG_DIR)