import argparse
from eo.base_image_collection import BaseImageCollection
from eo.image_utils import search_catalog
from eo.utils import set_up_dask, load_config
from eo.modes import single, multi

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
    set_up_dask()

    parser = argparse.ArgumentParser(
        description=("Get the best image/s based on XY and date range"),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--mode", required=True, type=str)
    parser.add_argument("--type", required=False, type=str) # TODO Make --type=clip boolean
    # For annotation
    parser.add_argument('--annt', default=False, action=argparse.BooleanOptionalAction)
    # For histogram mode
    parser.add_argument("--tif", required=False, type=str)
    parser.add_argument("--bn", required=False, type=str)
    parser.add_argument("--lo", required=False, type=str)
    parser.add_argument("--up", required=False, type=bool)
    args = parser.parse_args()

    mode = args.mode
    tif = args.tif
    bn = args.bn
    lo = args.lo
    up = args.up
    up = args.up
    type = args.type
    annt = args.annt

    if mode == 'single':
        single.run(image_selection=IMAGE_RESULTS, type=type, annt=annt)

    elif mode == 'multi':
        multi.run(image_selection=IMAGE_RESULTS, type=type, annt=annt)

    elif mode == 'hist':
        pass # Temporarily disable until AnnotatedImage is fully working
        # hist.run(bn=bn, tif=tif, lo=lo, up=up, out=out)
        