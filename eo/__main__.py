import argparse
import json
from . import PROJECT_DIR
from eo.logger import logger
from eo.modes.basic import BasicMode

if __name__ == "__main__":
    log = logger(PROJECT_DIR / 'logs/eo.log')
    log.info('STARTED EO')

    parser = argparse.ArgumentParser(
        description=("Get the best image/s based on XY and date range"),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("payload_json", help="See sample JSON file in data/")

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

    payload = args.payload_json
    with open(payload, 'r') as f:
        payload_dict = json.load(f)

    START_DATE = payload_dict['start_date']
    END_DATE = payload_dict['end_date']
    LATITUDE = float(payload_dict['latitude'])
    LONGITUDE = float(payload_dict['longitude'])
    BUFFER = float(payload_dict['buffer'])
    FREQUENCY = payload_dict['frequency']
    ANNOTATE = payload_dict['annotate']
    BOUNDARY = payload_dict['boundary']
    ALL = payload_dict['all']
    TO_ZIP = payload_dict['to_zip']

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
        "all": ALL,
        "to_zip": TO_ZIP
    })
    basic_mode.run()