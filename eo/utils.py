from dask_gateway import Gateway
import yaml
from pathlib import Path

def load_config(path):
    with open(Path(path), "r") as f:
        return yaml.safe_load(f)


def set_up_dask(enabled=False, dashboard=False, num_workers=4, min_workers=4, max_workers=50):
    if enabled:
        gateway = Gateway("http://127.0.0.1:8000")
        gateway.list_clusters()

        cluster = gateway.new_cluster()
        cluster.scale(num_workers)

        cluster.get_client()
        cluster.adapt(minimum=min_workers, maximum=max_workers)

        if dashboard:
            return cluster.dashboard_link


def simplify_datetime(date):
    from datetime import datetime

    dt = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ')
    return dt.strftime('%Y %B %d %-I:%M%p')