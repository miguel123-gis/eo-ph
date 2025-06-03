import pystac
import pystac.item
import pystac.item_collection
import pystac_client
import planetary_computer
import geopandas as gpd
import rioxarray
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


def stretch_contrast():
    pass

def stack_rgb_arrays():
    pass

def post_process():
    pass

def export_to_tif():
    pass