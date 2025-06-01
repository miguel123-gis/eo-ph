from eo.base_image import BaseImage
from eo.utils import set_up_dask

BANDS_SELECTION = {
    'red': 'B04',
    'green': 'B03',
    'blue': 'B02'
}

if __name__ == "__main__":
    set_up_dask(enabled=True)

    image = BaseImage(
        start_date = '2025-04-01',
        end_date = '2025-04-30',
        lon = 123.30178949703331,
        lat = 13.513854650838848,
        collection = 'sentinel-2-l2a'
    )

    image_collection = image.search_collection()
    best_image = image.get_image(image_collection)
    rgb_bands = image.get_individual_bands(best_image, BANDS_SELECTION)