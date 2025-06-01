import pystac_client
import planetary_computer
from  eo.utils import set_up_dask

set_up_dask(enabled=True)

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

        return search.item_collection()

    def get_image(self):
        pass

    def get_rgb_bands(self):
        pass

    def convert_to_arrays(self):
        pass

    def stretch_contrast(self):
        pass

    def stack_rgb_arrays(self):
        pass

    def post_process(self):
        pass

    def export_to_tif(self):
        pass



