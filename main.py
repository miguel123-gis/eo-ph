import argparse
import rioxarray
from eo.base_image_collection import BaseImageCollection
from eo.base_image import BaseImage
from eo.image_utils import search_catalog, get_best_image, get_individual_bands
from eo.utils import set_up_dask, load_config

config = load_config('config.yaml')

BANDS_SELECTION = config['bands']
SLICE = slice(config['slice_start'], config['slice_end'])
LOWER_PERC = config['lower_percentile']
UPPER_PERC = config['upper_percentile']
NO_DATA_VAL = config['no_data_value']
GAMMA_CORRECTION = config['gamma_correction']

def run_tasks(**kwargs):
    out_file = kwargs.get('out_file')

    image_collection = BaseImageCollection(
        start_date = '2025-04-01',
        end_date = '2025-04-30',
        lon = 123.30178949703331,
        lat = 13.513854650838848,
        collection = 'sentinel-2-l2a'
    )

    image_results = search_catalog(image_collection)
    best_image = get_best_image(image_results)
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
        .process_stack(gamma=GAMMA_CORRECTION)
    )

    image.get_rgb_stack(export=out_file)


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

    if mode == 'run':
        set_up_dask(enabled=True)
        run_tasks(out_file=out)

    elif mode == 'hist':
        BaseImage._plot_histogram_with_percentiles(
            band_name=bn,
            band_array=rioxarray.open_rasterio(tif),
            lower=int(lo), upper=int(up),
            figsize=(8,4),
            out_file=out
        )
        