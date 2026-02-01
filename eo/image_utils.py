import pystac
import pystac_client
import planetary_computer
import pandas as pd
import duckdb
import requests
from pathlib import Path
from shapely.geometry import box
from eo.dataclasses.base_image_collection import BaseImageCollection
from eo.constants import FREQUENCY_MAP
from typing import List

def search_catalog(imgcol: BaseImageCollection) -> pystac.item.Item:
    """Search a collection e.g. Sentintel 2 based on XY and date range."""
    date_range = f'{imgcol.start_date}/{imgcol.end_date}'
    xy = {
        'type': 'Point',
        'coordinates': [imgcol.lon, imgcol.lat]
    }

    catalog = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace
    )

    search = catalog.search(
        collections=[imgcol.collection],
        intersects=xy,
        datetime=date_range
    )

    return search.item_collection()

def get_best_image(image_selection) -> pystac.item.Item:
    """Selects the image with the lowest cloud cover from the image collection."""
    best_image = min(image_selection, key=lambda item: item.properties["eo:cloud_cover"])

    return best_image


def get_best_images(image_selection, frequency='yearly') -> pystac.item_collection.ItemCollection:
    """Selects the image with the lowest cloud cover per month from the image collection."""
    ic = pystac.item_collection
    temp_df = pd.DataFrame([result.to_dict() for result in image_selection]) 
    frequency = FREQUENCY_MAP.get(frequency)

    capture_date = temp_df.properties.str['datetime'].rename('capture_date') # Unnest capture date and cloud cover inside 'properties'
    cloud_cover = temp_df.properties.str['eo:cloud_cover'].rename('cloud_cover')

    add_cols = pd.concat([capture_date, cloud_cover], axis=1)
    add_cols_df = pd.DataFrame(add_cols) # Create a DF of the two columns
    add_cols_df['capture_date'] = pd.to_datetime(add_cols_df['capture_date'])
    concat_dfs = pd.concat([temp_df, add_cols_df], axis=1) # Add back the created DF to the original DF 

    best_images_df = concat_dfs.loc[ # Group by month and get the item with lowest cloud cover
        concat_dfs.groupby(pd.Grouper(key='capture_date', axis=0, freq=frequency)).cloud_cover.idxmin()
    ]
    best_images_ids = best_images_df['id'].to_list()

    best_images = [
        item
        for item in image_selection
        if any(item.id in image_id for image_id in best_images_ids)
    ]

    return ic.ItemCollection(best_images)


def get_bbox_from_point(x:float, y:float, source_crs:int, target_crs:int, bbox_size:int) -> box:
    """Return a shapely box created from the minimum and maximum XY of the bounding box of the buffer from the given point"""
    conn = duckdb.connect()

    query = f"""
        INSTALL spatial; LOAD spatial;

        WITH geom AS (
            SELECT 
                ST_Envelope(
                    ST_Buffer(
                        ST_Transform(
                            ST_Point({x}, {y}), 
                            'EPSG:{source_crs}',
                            'EPSG:{target_crs}',
                            always_xy := true
                        ),
                    {bbox_size}
                    )
                ) AS geom
            )
        SELECT 
            ST_XMin(geom) AS xmin, 
            ST_YMin(geom) AS ymin,
            ST_XMax(geom) AS xmax,
            ST_YMax(geom) AS ymax,
        FROM geom;
    """

    bounds = conn.sql(query).fetchall()[0]

    return box(bounds[0], bounds[1], bounds[2], bounds[3])

# NOTE See https://planetarycomputer.microsoft.com/api/stac/v1/collections/sentinel-2-l2a for reference
def get_collection_bands(collection_name) -> List:
    """Returns a list of bands available for a collection"""
    response = requests.get(f'https://planetarycomputer.microsoft.com/api/stac/v1/collections/{collection_name}')
    response.raise_for_status()
    item_assets = response.json()['item_assets']
    return [
        band for band in item_assets 
        if item_assets[band].get('eo:bands') # For regular bands
        or band == 'SCL'
    ]