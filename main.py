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

    parser.add_argument("--mode", required=True, type=str) # Single or multi
    parser.add_argument("--freq", required=False, type=str) # Monthly, yearly, etc.
    # Switches
    parser.add_argument('--clip', default=False, action=argparse.BooleanOptionalAction) # Clip images
    parser.add_argument('--annt', default=False, action=argparse.BooleanOptionalAction) # Annotate images
    parser.add_argument('--all', default=False, action=argparse.BooleanOptionalAction) # Export all assets (true color and bands)
    parser.add_argument('--bdry', default=False, action=argparse.BooleanOptionalAction) # Plot boundaries
    # For histogram mode
    parser.add_argument("--tif", required=False, type=str)
    parser.add_argument("--bn", required=False, type=str)
    parser.add_argument("--lo", required=False, type=str)
    parser.add_argument("--up", required=False, type=bool)
    args = parser.parse_args()

    mode = args.mode
    freq = args.freq
    tif = args.tif
    bn = args.bn
    lo = args.lo
    up = args.up
    up = args.up
    clip = args.clip
    annt = args.annt
    all = args.all
    bdry = args.bdry

    if mode == 'single':
        single.run(image_selection=IMAGE_RESULTS, clip=clip, annt=annt, all=all, bdry=bdry)

    elif mode == 'multi':
        multi.run(image_selection=IMAGE_RESULTS, freq=freq, clip=clip, annt=annt, all=all, bdry=bdry)

    elif mode == 'hist':
        pass # Temporarily disable until AnnotatedImage is fully working
        # hist.run(bn=bn, tif=tif, lo=lo, up=up, out=out)
        