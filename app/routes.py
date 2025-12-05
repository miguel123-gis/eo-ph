
from pathlib import Path
from celery import Celery, result
from flask import Flask, request, jsonify, render_template, send_file, redirect, url_for
from eo.logger import logger
from eo.modes.basic import BasicMode
from eo.constants import REQUIRED_PARAMETERS

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

@app.route("/download", methods=['GET', 'POST'])
def download():
    data = request.form.to_dict()
    log.info(data)

    if len(data) > 0:
        log.info('CALLING FROM /download')
        for param in REQUIRED_PARAMETERS:
            data.setdefault(param, False)
        data['to_zip'] = True
        async_task = call_download.delay(data)
        out_file_after = async_task.get()
        # NOTE Is OUT_FILE still None at this point?
        return send_file(out_file_after, as_attachment=True)
    
    # TODO Add logger/handling
    return render_template('form.html') # TODO Redirect to success page e.g. /download/<folder> so I can do return send_file(OUT_FILE, as_attachment=True)

@app.route('/api/download', methods=['GET', 'POST'])
def api_download():
    data = request.get_json(silent=True)
    
    if len(data) > 0:
        log.info('CALLING FROM /api/download')
        async_task = call_download.delay(data)
        return jsonify({"status": "ok", "received": data, "async_id": async_task.id})
    
    if data is None:
        return jsonify({"status": "error", "message": 'No data received', "async_id": async_task.id})
    
@celery.task(bind=True)
def call_download(self, data):
    with app.app_context():
        if len(data) > 0:
            task_id = self.request.id
            log.info(f"TASK ID: {task_id}")

            try:
                basic_mode = BasicMode(data)
                out_file = basic_mode.run()
                log.info(f"TASK {task_id}: {result.AsyncResult(task_id).state}") # TODO Task state is always pending, see https://stackoverflow.com/questions/27357732/celery-task-always-pending
                return str(out_file) # Need to stringify due to kombu.exceptions.EncodeError: TypeError('Object of type PosixPath is not JSON serializable')
            except Exception as e:
                log.error(f"TASK {task_id}: {result.AsyncResult(task_id).state}", exc_info=True)

        else:
            log.error('Empty/incomplete payload', exc_info=True)
            raise ValueError('Empty/incomplete payload')
    
@celery.task
def test_celery():
    log.info('CELERY IS WORKING')

if __name__ == "__main__":
    app.run(host='0.0.0.0')