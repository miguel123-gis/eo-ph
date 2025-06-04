from eo.base_image_collection import BaseImageCollection
from eo.base_image import BaseImage
from eo.image_utils import search_catalog, get_best_image, get_individual_bands
from eo.utils import set_up_dask

BANDS_SELECTION = {
    'red': 'B04',
    'green': 'B03',
    'blue': 'B02'
}

if __name__ == "__main__":
    set_up_dask(enabled=True)

    image_collection = BaseImageCollection(
        start_date = '2025-04-01',
        end_date = '2025-04-30',
        lon = 123.30178949703331,
        lat = 13.513854650838848,
        collection = 'sentinel-2-l2a'
    )

    image_results = search_catalog(image_collection)
    best_image = get_best_image(image_results)
    rgb_bands = get_individual_bands(
        best_image, 
        BANDS_SELECTION,
        subset=slice(5000,6000)
    )

    image = (
        BaseImage(bands=rgb_bands, lower=0.02, upper=0.98, no_data_value=0)
        .plot_histogram_with_percentiles()
        .stretch_contrast()
        .stack_bands(['red', 'green', 'blue'])
        .process_stack()
    )

    rgb = image.get_rgb_stack(export='data/processed/rgb_v2.tif')