from dask_gateway import Gateway
import yaml
from pathlib import Path
import geopandas as gpd
import pandas as pd

def load_config(path):
    with open(Path(path), "r") as f:
        return yaml.safe_load(f)


def set_up_dask(dashboard=False, num_workers=4, min_workers=4, max_workers=50):
    gateway = Gateway("http://127.0.0.1:8000")
    gateway.list_clusters()

    cluster = gateway.new_cluster()
    cluster.scale(num_workers)

    cluster.get_client()
    cluster.adapt(minimum=min_workers, maximum=max_workers)

    if dashboard:
        return cluster.dashboard_link


def simplify_datetime(date, compact=False):
    from datetime import datetime

    dt = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ')

    if compact:
        return dt.strftime('%Y-%m-%d-%H%M')
    
    return dt.strftime('%Y %B %d %-I:%M%p')


def list_intersecting_municipalities(municipalities: gpd.GeoDataFrame):
    """Return the province with the highest total area of intersection and its top 3 municipalities."""
    municipalities["area"] = municipalities.geometry.area 

    # Sum total area per province
    province_area = (
        municipalities.groupby("NAME_1")["area"]
        .sum()
        .sort_values(ascending=False)
    )

    # Get the province with greatest intersection
    top_province = province_area.idxmax()

    # Get the municipalities in top_province
    top_rows = municipalities[municipalities["NAME_1"] == top_province]

    # Get top 3 municipalities in that province by area
    top_munis = (
        top_rows[["NAME_2", "area"]]
        .sort_values("area", ascending=False)
        .head(3)["NAME_2"]
        .tolist()
    )

    return {
        "province": top_province,
        "towns": top_munis
    }