from dask.distributed import Client, LocalCluster
import yaml
from pathlib import Path
import geopandas as gpd
import pandas as pd

def load_config(path):
    with open(Path(path), "r") as f:
        return yaml.safe_load(f)


def set_up_dask(dashboard=False, num_workers=4, min_workers=4, max_workers=50):
    cluster = LocalCluster(host="0.0.0.0", n_workers=4)
    client = Client(cluster)

    if dashboard:
        return 'http://localhost:8787/status' # TODO Pass port number as Docker env
    
    return client


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