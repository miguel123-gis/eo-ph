import pystac
import pystac.item
import pystac.item_collection
import pystac_client
import planetary_computer
import pandas as pd
import rioxarray
import xarray
from typing import Dict, Union
from eo.base_image_collection import BaseImageCollection

def search_catalog(imgcol: BaseImageCollection) -> pystac.item_collection.ItemCollection:
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

    search_results = search.item_collection()

    return search_results
    

def get_best_image(image_selection) -> pystac.item.Item:
    """Selects the image with the lowest cloud cover from the image collection."""
    best_image = min(image_selection, key=lambda item: item.properties["eo:cloud_cover"])

    return best_image


def get_best_images(image_selection, interval='monthly') -> pystac.item_collection.ItemCollection:
    """Selects the image with the lowest cloud cover per month from the image collection."""
    ic = pystac.item_collection
    temp_df = pd.DataFrame([result.to_dict() for result in image_selection]) 
    frequency = 'YE' if interval == 'yearly' else 'ME'

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


def get_individual_bands(image, band_nums:Dict, subset: Union[bool, slice, None] = False) -> Dict:
    """Get the individual bands (e.g. Red, Green, and Blue) from the selected image."""
    assets = image.assets

    bands = {
        name: rioxarray.open_rasterio(url.href, chunks=True)
        for name, band_num in band_nums.items()
        for band, url in assets.items()
        if band_num == band
    }

    if subset:
        bands_subset = {
            name: band.isel(x=subset, y=subset)
            for name, band in bands.items()
        }

        return bands_subset

    return bands


def get_visual_asset(image: pystac.Item, subset: Union[bool, slice, None] = False) -> xarray.DataArray:
    va_array = rioxarray.open_rasterio(image.assets['visual'].href)

    if subset:
        subset_ar = va_array.isel(x=subset, y=subset)

        return subset_ar

    return va_array