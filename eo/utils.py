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
    """Given a GeoDataFrame that's clipped to a raster's extent, list the municipalities and province based on intersection"""
    area_temp = municipalities.geometry.area.rename('area')
    with_area = pd.concat([municipalities, area_temp], axis=1)[['NAME_1', 'NAME_2', 'area']].sort_values("area", ascending=False)

    agg_df = (
        with_area.groupby("NAME_1")["NAME_2"]
        .apply(lambda x: ", ".join(x))
        .reset_index(name="muni_sorted")
        .rename(columns={"NAME_1": "province"})
    )

    return  {
        'towns': agg_df['muni_sorted'].to_list()[0].split(',')[:3],
        'province': agg_df['province'].item()
    }