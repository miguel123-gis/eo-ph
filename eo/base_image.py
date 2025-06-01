import pystac_client
import planetary_computer
import geopandas as gpd
import rioxarray


class BaseImage:
    def __init__(self, start_date, end_date, lat, lon, collection):
        self.start_date = start_date
        self.end_date = end_date
        self.lat = lat
        self.lon = lon
        self.collection = collection


    def search_collection(self):
        date_range = f'{self.start_date}/{self.end_date}'
        xy = {
            'type': 'Point',
            'coordinates': [self.lon, self.lat]
        }

        catalog = pystac_client.Client.open(
            "https://planetarycomputer.microsoft.com/api/stac/v1",
            modifier=planetary_computer.sign_inplace
        )

        search = catalog.search(
            collections=[self.collection],
            intersects=xy,
            datetime=date_range
        )

        search_results = search.item_collection()

        return search_results
    

    def get_image(self, image_selection):
        selected_image = min(image_selection, key=lambda item: item.properties["eo:cloud_cover"])

        return selected_image
    

    def get_individual_bands(self, image, band_nums:dict, subset=False):
        assets = image.assets

        bands = {
            name: rioxarray.open_rasterio(url.href, chunks=True)
            for name, band_num in band_nums.items()
            for band, url in assets.items()
            if band_num == band
        }

        return bands
    

    def stretch_contrast(self):
        pass

    def stack_rgb_arrays(self):
        pass

    def post_process(self):
        pass

    def export_to_tif(self):
        pass



