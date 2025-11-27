import argparse
import time
from pathlib import Path
from eo.logger import logger
from eo.base_image_collection import BaseImageCollection
from eo.image_utils import search_catalog
from eo.utils import load_config
from eo.modes import basic

PROJECT_DIR = Path(__file__).resolve().parent.parent
CONFIG = load_config('config.yaml')

START_DATE = CONFIG['start_date']
END_DATE = CONFIG['end_date']
LONGITUDE = float(CONFIG['longitude'])
LATITUDE = float(CONFIG['latitude'])
BUFFER = float(CONFIG['buffer_size_meters'])

IMAGE_COLLECTION = BaseImageCollection(
    start_date = START_DATE,
    end_date = END_DATE,
    lon = LONGITUDE,
    lat = LATITUDE,
    collection = 'sentinel-2-l2a'
)

IMAGE_RESULTS = search_catalog(IMAGE_COLLECTION)

if __name__ == "__main__":
    start_time = time.time()
    log = logger(PROJECT_DIR / 'logs/eo.log')
    log.info('STARTED EO')

    parser = argparse.ArgumentParser(
        description=("Get the best image/s based on XY and date range"),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--mode", required=True, type=str) # Basic or histogram (currently disabled)
    parser.add_argument("--freq", required=False, type=str) # Monthly, yearly, etc.
    # Switches
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
    annt = args.annt
    all = args.all
    bdry = args.bdry

    # For histogram mode
    # tif = args.tif
    # bn = args.bn
    # lo = args.lo
    # up = args.up

    if mode == 'basic':
        basic.run(
            IMAGE_RESULTS, float(LONGITUDE), float(LATITUDE), float(BUFFER), frequency=freq,
            annotate=annt, export_all=all, plot_boundary=bdry
        ) 

    elif mode == 'hist':
        pass # Temporarily disable until AnnotatedImage is fully working
        # hist.run(bn=bn, tif=tif, lo=lo, up=up, out=out)

    end_time = time.time()
    log.info(f"FINISHED IN {round(end_time-start_time, 2)} SECONDS")