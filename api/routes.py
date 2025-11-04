from flask import Flask, request, jsonify, render_template
from eo.logger import logger
from eo.base_image_collection import BaseImageCollection
from eo.image_utils import search_catalog
from eo.utils import set_up_dask, load_config, safe_close
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
        log.info('CALLING FROM /download')
        call_download(data)
    
    return render_template('form.html')

@routes.route('/api/download', methods=['POST'])
def api_download():
    data = request.get_json(silent=True)
    
    if len(data) > 0:
        log.info('CALLING FROM /api/download')
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
    log.info(buffer is True)
    mode = data.get("mode")
    # Optional arguments
    freq = data.get("frequency")
    annt = data.get("annotate")
    all = data.get("all")
    bdry = data.get("boundary")

    if len(data) > 0:
        log.info('STARTED EO')
        log.info(f"RECEIVED {data}")
        cluster, client, dashboard = set_up_dask(dashboard=True)
        safe_close(client, cluster)
        
        log.info(f'DASK DASHBOARD: {dashboard}')

        log.info(f'GETTING IMAGES INTERSECTING {lon}, {lat} FROM {start} TO {end}')

        if mode == 'single':
            log.info('RUNNING IN SINGLE MODE, ONLY GETTING THE IMAGE WITH LEAST CLOUD COVER IN DATE RANGE')
        elif mode == 'multi' and freq:
            log.info(f'RUNNING IN MULTI MODE, GETTING IMAGE WITH LEAST CLOUD COVER IN DATE RANGE {freq.upper()}')
            
        if buffer and int(buffer) > 0:
            clip = True
            log.info(f'ONLY GETTING AREA {buffer} METERS FROM XY')
        else:
            clip = False

        # TODO Currently disabled due to plt.subplot() multithreading crash
        if all is True:
            log.info('GETTING THE RED, GREEN, BLUE AND TRUE-COLOR IMAGES')
        
        if annt is True:
            log.info('INCLUDING MAP ANNOTATIONS E.G. CAPTURE DATE, CLOUD COVER, ETC.')

        if bdry is True:
            log.info('PLOTTING BOUNDARIES IN EXPORTS')

        # Insert logic for single and multi mode
        IMAGE_COLLECTION = BaseImageCollection(
            start_date = start,
            end_date = end,
            lon = lon,
            lat = lat,
            collection = 'sentinel-2-l2a'
        )

        IMAGE_RESULTS = search_catalog(IMAGE_COLLECTION)
        log.info(f'GOT {len(IMAGE_RESULTS)} IMAGES TO SELECT FROM')

        if mode == 'single':
            single.run(image_selection=IMAGE_RESULTS, clip=clip, annt=annt, all=all, bdry=bdry) 
            log.info('DONE RUN IN SINGLE MODE')

        elif mode == 'multi':
            multi.run(image_selection=IMAGE_RESULTS, freq=freq, clip=clip, annt=annt, all=all, bdry=bdry)
            log.info('DONE RUN IN MULTI MODE')
    
        cluster.close()
        client.close()