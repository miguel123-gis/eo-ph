from eo.base_image import BaseImage

if __name__ == "__main__":
    image = BaseImage(
        start_date = '2025-04-01',
        end_date = '2025-04-30',
        lon = 123.30178949703331,
        lat = 13.513854650838848,
        collection = 'sentinel-2-l2a'
    )

    items = image.search_collection()