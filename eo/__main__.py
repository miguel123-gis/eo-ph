import argparse
from pathlib import Path
from eo.logger import logger
from eo.utils import load_config
from eo.modes.basic import BasicMode

PROJECT_DIR = Path(__file__).resolve().parent.parent
CONFIG = load_config('config.yaml') # TODO Add handle if config.yaml is not existing

START_DATE = CONFIG['start_date']
END_DATE = CONFIG['end_date']
LONGITUDE = float(CONFIG['longitude'])
LATITUDE = float(CONFIG['latitude'])
BUFFER = float(CONFIG['buffer_size_meters'])
FREQUENCY = CONFIG['frequency']
ANNOTATE = CONFIG['annotate']
BOUNDARY = CONFIG['boundary']
ALL = CONFIG['all']

if __name__ == "__main__":
    log = logger(PROJECT_DIR / 'logs/eo.log')
    log.info('STARTED EO')

    parser = argparse.ArgumentParser(
        description=("Get the best image/s based on XY and date range"),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # For histogram mode
    parser.add_argument("--hist", required=False, type=str)
    parser.add_argument("--tif", required=False, type=str)
    parser.add_argument("--bn", required=False, type=str)
    parser.add_argument("--lo", required=False, type=str)
    parser.add_argument("--up", required=False, type=bool)
    args = parser.parse_args()

    # NOTE # Temporarily disabled until AnnotatedImage is fully working
    # For histogram mode
    # hist = args.hist
    # tif = args.tif
    # bn = args.bn
    # lo = args.lo
    # up = args.up
    # if hist: 
        # hist.run(bn=bn, tif=tif, lo=lo, up=up, out=out)

    log.info('CALLING VIA CLI')
    basic_mode = BasicMode({
        "start_date": START_DATE,
        "end_date": END_DATE,
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "buffer": BUFFER,
        "frequency": FREQUENCY,
        "annotate": ANNOTATE,
        "boundary": BOUNDARY,
        "all": ALL
    })
    basic_mode.run()