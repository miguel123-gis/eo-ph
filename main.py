import argparse
from eo.base_image_collection import BaseImageCollection
from eo.image_utils import search_catalog
from eo.utils import set_up_dask, load_config
from eo.modes import single, multi, hist

CONFIG = load_config('config.yaml')

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
    parser.add_argument("--type", required=False, type=str)
    args = parser.parse_args()

    mode = args.mode
    out = args.out
    tif = args.tif
    bn = args.bn
    lo = args.lo
    up = args.up
    up = args.up
    type = args.type

    if mode == 'single':
        set_up_dask(enabled=True)
        single.run(image_selection=IMAGE_RESULTS, out_file=out, type=type)

    elif mode == 'multi':
        set_up_dask(enabled=True)
        multi.run(image_selection=IMAGE_RESULTS)

    elif mode == 'hist':
        hist.run(bn=bn, tif=tif, lo=lo, up=up, out=out)
        