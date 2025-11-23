from pathlib import Path
import numpy as np
from eo.base_image import BaseImage
from eo.annotated_image import AnnotatedImage
from eo.image_utils import get_best_image, get_bbox_from_point
from eo.utils import load_config

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent # eo-ph/
CONFIG = load_config(PROJECT_DIR / 'config.yaml')

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

def run(image_selection, longitude, latitude, buffer, **kwargs):
    annotate = kwargs.get('annt')
    export_all = kwargs.get('all')
    plot_boundary = kwargs.get('bdry')
    assets = {**BANDS_SELECTION, 'true_color': 'visual'}
    bbox = get_bbox_from_point(longitude, latitude, 4326, 32651, buffer*1000)
    best_image = get_best_image(image_selection)

    if buffer > 0:
        base_img = BaseImage(
                image_item=best_image, 
                band_nums=BANDS_SELECTION, 
                subset=True, 
                assets=assets, 
                bbox=bbox
            )
    else:
        base_img = BaseImage(image_item=best_image, band_nums=BANDS_SELECTION, true_color=True)
        
    if annotate:
        annt_img = AnnotatedImage(base_image=base_img)
        annt_img.annotate(
            boundaries=PH_BDRYS, out_dir=PROCESSED_IMG_DIR, 
            lon=longitude, lat=latitude,
            plot_bdry=plot_boundary,
            figsize=FIGSIZE, dpi=DPI
        )
    else:
        if export_all:
            base_img.export(export_rgb=True, out_dir=PROCESSED_IMG_DIR)
        else:
            base_img.export(out_dir=PROCESSED_IMG_DIR)
