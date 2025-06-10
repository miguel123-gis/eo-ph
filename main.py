import argparse
import rioxarray
import numpy as np
from eo.base_image_collection import BaseImageCollection
from eo.base_image import BaseImage
from eo.image_utils import search_catalog
from eo.utils import set_up_dask, load_config
from eo.modes import single, multi

CONFIG = load_config('config.yaml')

DTYPE_MAP = {
    'uint8': np.uint8,
    'uint16': np.uint16,
    'float32': np.float32,
}

PROCESSED_IMG_DIR = 'data/processed'
BANDS_SELECTION = CONFIG['bands']
START_DATE = CONFIG['start_date']
END_DATE = CONFIG['end_date']
LONGITUDE = float(CONFIG['longitude'])
LATITUDE = float(CONFIG['latitude'])

IMAGE_COLLECTION = BaseImageCollection(
    start_date = START_DATE,
    end_date = END_DATE,
    lon = LONGITUDE,
    lat = LATITUDE,
    collection = 'sentinel-2-l2a'
)

IMAGE_RESULTS = search_catalog(IMAGE_COLLECTION)

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
        # run_tasks_single(out_file=out)
        single.run(image_selection=IMAGE_RESULTS, out_file=out)

    elif mode == 'multi':
        set_up_dask(enabled=True)
        multi.run(image_selection=IMAGE_RESULTS)

    elif mode == 'hist':
        BaseImage._plot_histogram_with_percentiles(
            band_name=bn,
            band_array=rioxarray.open_rasterio(tif),
            lower=int(lo), upper=int(up),
            figsize=(8,4),
            out_file=out
        )
        