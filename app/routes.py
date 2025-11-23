import os
import time
from pathlib import Path
from celery import Celery
from flask import Flask, request, jsonify, render_template
from eo.logger import logger
from eo.base_image_collection import BaseImageCollection
from eo.image_utils import search_catalog
from eo.utils import set_up_dask, safe_close
from eo.modes import single, multi

PROJECT_DIR = Path(__file__).resolve().parent.parent

app = Flask(__name__)
celery = Celery(
    __name__,
    broker="redis://redis:6379/0", # TODO Add this as a config e.g. if ran in local then broker="redis://127.0.0.1:6379/0",
    backend="redis://redis:6379/0"
)
log = logger(PROJECT_DIR / 'logs/eo.log')

@app.route('/')
def hello():
    return '<h1>Hello, World!</h1>'

@app.route("/download", methods=['GET', 'POST'])
def download():
    data = request.form.to_dict()

    if len(data) > 0:
        log.info('CALLING FROM /download')
        call_download(data)
    
    return render_template('form.html')

@app.route('/api/download', methods=['GET', 'POST'])
def api_download():
    data = request.get_json(silent=True)
    
    if len(data) > 0:
        log.info('CALLING FROM /api/download')
        call_download.delay(data)
        return jsonify({"status": "ok", "received": data})
    
    if data is None:
        return jsonify({"status": "error", "message": 'No data received'})

@celery.task
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
    annt = data.get("annotate")
    all = data.get("all")
    bdry = data.get("boundary")
    workers = data.get("workers")

    if workers is None:
        workers = os.cpu_count()-1

    if len(data) > 0:
        start_time = time.time()
        log.info(f'STARTED EO WITH {workers} WORKERS')
        log.info(f"RECEIVED {data}")
        cluster, client, dashboard = set_up_dask(dashboard=True, num_workers=int(workers))
        safe_close(client, cluster)
        
        log.info(f'DASK DASHBOARD: {dashboard}')

        log.info(f'GETTING IMAGES INTERSECTING {lon}, {lat} FROM {start} TO {end}')

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

            single.run(
                IMAGE_RESULTS, float(lon), float(lat), float(buffer), 
                annotate=annt, export_all=all, plot_boundary=bdry
            ) 
            log.info('DONE RUN IN SINGLE MODE')

        elif mode == 'multi':
            multi.run(
                IMAGE_RESULTS, float(lon), float(lat), float(buffer), freq,
                annotate=annt, export_all=all, plot_boundary=bdry
            )
            log.info('DONE RUN IN MULTI MODE')

        end_time = time.time()
        log.info(f"FINISHED IN {round(end_time-start_time, 2)} SECONDS")
    
        cluster.close()
        client.close()

if __name__ == "__main__":
    app.run(host='0.0.0.0')