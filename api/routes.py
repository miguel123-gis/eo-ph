from flask import Flask, request, jsonify, render_template
from eo.logger import logger
from eo.base_image_collection import BaseImageCollection
from eo.image_utils import search_catalog
from eo.utils import set_up_dask, load_config
from eo.modes import single, multi

routes = Flask(__name__)
log = logger('eo.log')

@routes.route('/')
def hello():
    return '<h1>Hello, World!</h1>'

@routes.route("/download", methods=['GET', 'POST'])
def download():
    data = request.form.to_dict()

    if len(data) > 0:
        call_download(data)
    
    return render_template('form.html')

@routes.route('/api/download', methods=['POST'])
def api_download():
    data = request.get_json(silent=True)
    
    if len(data) > 0:
        call_download(data)
        return jsonify({"status": "ok", "received": data})
    
    if data is None:
        return jsonify({"status": "error", "message": 'No data received'})

def call_download(data):
    # Required arguments
    start = data.get("start_date")
    end = data.get("end_date")
    lat = data.get("latitude")
    lon = data.get("longitude")
    buffer = data.get("buffer", 3)
    mode = data.get("mode")
    # Optional arguments
    freq = data.get("frequency")
    clip = data.get("clip")
    annt = data.get("annotate")
    all = data.get("all")
    bdry = data.get("boundary")

    if len(data) > 0:
        log.info('STARTED EO')
        log.info(f"RECEIVED {data}")
        dashboard = set_up_dask(dashboard=True)
        log.info(f'DASK DASHBOARD: {dashboard}')

        # Insert logic for single and multi mode
        IMAGE_COLLECTION = BaseImageCollection(
            start_date = start,
            end_date = end,
            lon = lon,
            lat = lat,
            collection = 'sentinel-2-l2a'
        )

        IMAGE_RESULTS = search_catalog(IMAGE_COLLECTION)

        if mode == 'single':
            log.info('DONE')
            single.run(image_selection=IMAGE_RESULTS, clip=clip, annt=annt, all=all, bdry=bdry, log=log) 

        elif mode == 'multi':
            multi.run(image_selection=IMAGE_RESULTS, freq=freq, clip=clip, annt=annt, all=all, bdry=bdry)
            log.info('DONE')