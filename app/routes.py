import sys
from pathlib import Path
from celery import Celery
from celery.result import AsyncResult
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_file
from eo.logger import logger
from eo.modes.basic import BasicMode
from eo.modes.nocloud import NoCloudMode
from eo.dataclasses.payload import validate_payload, InvalidPayloadError, InvalidFrequencyError, InvalidModeError

PROJECT_DIR = Path(__file__).resolve().parent.parent

app = Flask(__name__)
celery = Celery(
    __name__,
    broker="redis://redis:6379/0", # TODO Add this as a config e.g. if ran in local then broker="redis://127.0.0.1:6379/0",
    backend="redis://redis:6379/0"
)
log = logger(PROJECT_DIR / 'logs/eo.log')


@app.route('/')
def index():
    return '<h1>Hello, World!</h1>'

@app.route('/download/<task_id>', methods=['GET'])
def download_result(task_id):
    result = AsyncResult(task_id)
    if result.ready():
        return send_file(result.get(), as_attachment=True)

    return render_template('download.html', task_id={"task_id": task_id})

@app.route('/status/<task_id>', methods=['GET'])
def task_status(task_id):
    result = AsyncResult(task_id)
    return jsonify({
        "ready": result.ready(),
        "success": result.state == 'SUCCESS',
        "result": result.get()
    })

@app.route("/download", methods=['GET', 'POST'])
def download():
    data = request.form.to_dict()

    if len(data) > 0:
        log.info(f"PAYLOAD: {data}")
        validated = validate_payload(data)
        log.info(f"VALIDATED: {validated}")

        log.info('CALLING FROM /download')
        task = call_download.delay(validated)
        task_id = task.task_id
        return redirect(url_for('download_result', task_id=task_id))
   
    # TODO Add logger/handling
    return render_template('form.html')

@app.route('/api/download', methods=['GET', 'POST'])
def api_download():
    data = request.get_json(silent=True)

    if len(data) > 0:
        log.info(f"PAYLOAD: {data}")
        validated = validate_payload(data)

        log.info('CALLING FROM /api/download')
        async_task = call_download.delay(validated)
        return jsonify({"status": "ok", "received": data, "async_id": async_task.id})
    
    if data is None:
        return jsonify({"status": "error", "message": 'No data received', "async_id": async_task.id})
    
@celery.task(bind=True)
def call_download(self, data):
    with app.app_context():
        with app.test_request_context():
            if len(data) > 0:
                task_id = self.request.id
                log.info(f"TASK ID: {task_id}")

                if data['cloudless']:
                    log.info('RUNNING IN CLOUDLESS MODE')
                    nocloud_mode = NoCloudMode(data)
                    out_file = nocloud_mode.run()
                    return str(out_file)
                else:
                    try:
                        log.info('RUNNING IN BASIC MODE')
                        basic_mode = BasicMode(data)
                        out_file = basic_mode.run()
                        return str(out_file)
                    except Exception as e:
                        log.error(f"TASK {task_id}: {AsyncResult(task_id).state}", exc_info=True)

            else:
                log.error('Empty/incomplete payload', exc_info=True)
                raise ValueError('Empty/incomplete payload')
            
@app.errorhandler(InvalidPayloadError)
@app.errorhandler(InvalidFrequencyError)
@app.errorhandler(InvalidModeError)
def handle_payload_errors(e):
    response = jsonify({"status": "error", "message": e.message})
    response.status_code = 400
    log.error(e.message)
    return response
    
@celery.task
def test_celery():
    log.info('CELERY IS WORKING')

if __name__ == "__main__":
    app.debug=True
    app.run(host='0.0.0.0')