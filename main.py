import argparse
import rioxarray
import numpy as np
from eo.base_image_collection import BaseImageCollection
from eo.base_image import BaseImage
from eo.image_utils import search_catalog, get_best_image, get_best_images, get_individual_bands
from eo.utils import set_up_dask, load_config

config = load_config('config.yaml')

DTYPE_MAP = {
    'uint8': np.uint8,
    'uint16': np.uint16,
    'float32': np.float32,
}

PROCESSED_IMG_DIR = 'data/processed'
BANDS_SELECTION = config['bands']
SLICE = slice(config['slice_start'], config['slice_end'])
LOWER_PERC = config['lower_percentile']
UPPER_PERC = config['upper_percentile']
NO_DATA_VAL = config['no_data_value']
MAX_VAL = config['maximum_value']
BIT_DEPTH = DTYPE_MAP.get(config['bit_depth'])
GAMMA_CORRECTION = config['gamma_correction']
CHUNK_SIZE = config['chunk_size']

IMAGE_COLLECTION = BaseImageCollection(
    start_date = '2025-04-01',
    end_date = '2025-04-30',
    lon = 123.30178949703331,
    lat = 13.513854650838848,
    collection = 'sentinel-2-l2a'
)

IMAGE_RESULTS = search_catalog(IMAGE_COLLECTION)

def run_tasks_single(**kwargs):
    out_file = kwargs.get('out_file')
    
    best_image = get_best_image(IMAGE_RESULTS)
    rgb_bands = get_individual_bands(
        best_image, 
        BANDS_SELECTION,
        subset=SLICE
    )

    image = (
        BaseImage(bands=rgb_bands, lower=LOWER_PERC, upper=UPPER_PERC, no_data_value=NO_DATA_VAL)
        .plot_histogram_with_percentiles()
        .stretch_contrast()
        .stack_bands(['red', 'green', 'blue'])
        .process_stack(max_val=MAX_VAL, gamma=GAMMA_CORRECTION, type=BIT_DEPTH, chunk=CHUNK_SIZE)
    )

    image.get_rgb_stack(export=out_file)


def run_tasks_multi(**kwargs):
    out_file = kwargs.get('out_file')
    best_images = get_best_images(IMAGE_RESULTS)
    processed_images = {}

    for image in best_images:
        rgb_bands = get_individual_bands(image, BANDS_SELECTION, subset=SLICE)

        processed_image = (
            BaseImage(bands=rgb_bands, lower=LOWER_PERC, upper=UPPER_PERC, no_data_value=NO_DATA_VAL)
            .stretch_contrast()
            .stack_bands(['red', 'green', 'blue'])
            .process_stack(max_val=MAX_VAL, gamma=GAMMA_CORRECTION, type=BIT_DEPTH, chunk=CHUNK_SIZE)
        )

        processed_images[image.id] = processed_image

    for name, image in processed_images.items():
        image.get_rgb_stack(export=f"{PROCESSED_IMG_DIR}/{name}.tif")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=("Get the best image based on XY and date range"),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--mode", required=True, type=str)
    parser.add_argument("--out", required=False, type=str)
    parser.add_argument("--tif", required=False, type=str)
    parser.add_argument("--bn", required=False, type=str)
    parser.add_argument("--lo", required=False, type=str)
    parser.add_argument("--up", required=False, type=str)
    args = parser.parse_args()

    mode = args.mode
    out = args.out
    tif = args.tif
    bn = args.bn
    lo = args.lo
    up = args.up

    if mode == 'single':
        set_up_dask(enabled=True)
        run_tasks_single(out_file=out)

    elif mode == 'multi':
        set_up_dask(enabled=True)
        run_tasks_multi(out_file=out)

    elif mode == 'hist':
        BaseImage._plot_histogram_with_percentiles(
            band_name=bn,
            band_array=rioxarray.open_rasterio(tif),
            lower=int(lo), upper=int(up),
            figsize=(8,4),
            out_file=out
        )
        