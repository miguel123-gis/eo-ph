
from pathlib import Path
from celery import Celery
from flask import Flask, request, jsonify, render_template
from eo.logger import logger
from eo.modes.basic import BasicMode

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
    test_celery.delay()
    return '<h1>Hello, World!</h1>'

@app.route("/download", methods=['GET', 'POST'])
def download():
    data = request.form.to_dict()

    if len(data) > 0:
        log.info('CALLING FROM /download')
        call_download.delay(data)
    
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
    if len(data) > 0:
        basic_mode = BasicMode(data)
        basic_mode.run()
    else:
        raise ValueError('Empty/incomplete payload')
    
@celery.task
def test_celery():
    log.info('CELERY IS WORKING')

if __name__ == "__main__":
    app.run(host='0.0.0.0')