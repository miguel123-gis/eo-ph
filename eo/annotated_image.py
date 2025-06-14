import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
import rioxarray as rxr
from eo.base_image import BaseImage
from eo.utils import simplify_datetime
from eo.image_utils import list_intersecting_municipalities

class AnnotatedImage:
    def __init__(
            self, 
            base_image: BaseImage,
            lower:float = None, upper:float = None, no_data_value:float = None
        ):
        self.image_id = base_image.image_item.id
        self.image_properties = base_image.image_item.properties
        self.bands = base_image.bands
        self.true_color = base_image.true_color
        self.extent = base_image.extent
        self.lower_percentile = lower
        self.upper_percentile = upper
        self.no_data_value = no_data_value


    def annotate(self, boundaries:gpd.GeoDataFrame, out_dir, **kwargs):
        """Add texts to a plot"""
        # Reorder the array for pyplot
        image = self.true_color.values
        image = np.moveaxis(image, 0, -1)

        # Get bbox and reorder extent for pyplot
        min_x, min_y, max_x, max_y = self.extent.bounds
        reordered_extent = (min_x, max_x, min_y, max_y)

        # Clip and reproject boundary layer
        boundaries = gpd.read_file(boundaries).to_crs(self.true_color.rio.crs)
        clipped_bdrys = boundaries.clip(self.extent)
        
        # Plot the raster and then vector
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(image, extent=reordered_extent)
        clipped_bdrys.boundary.plot(ax=ax, edgecolor='white', linewidth=0.15)    

        # Add text
        capture_date = simplify_datetime(self.image_properties['datetime'])
        platform = self.image_properties['platform']
        cloud_cover = self.image_properties['eo:cloud_cover']
        map_center = f"{round(kwargs.get('lon'), 3)}, {round(kwargs.get('lat'), 3)}"
        munis = ','.join(list_intersecting_municipalities(clipped_bdrys))

        plt.axis('off')
        plt.figtext(0.13, 0.09, f'From {platform} with image ID of {self.image_id}', ha='left', va='bottom', fontname='Helvetica', fontsize=10)
        plt.figtext(0.13, 0.07, f'Captured on {capture_date} with {int(cloud_cover)}% cloud cover', ha='left', va='bottom', fontname='Helvetica', fontsize=10)
        plt.figtext(0.13, 0.05, f'Covers {munis} with center at {map_center}', ha='left', va='bottom', fontname='Helvetica', fontsize=10)
        plt.savefig(f'{out_dir}/{self.image_id}.png', dpi=200)

        
    @staticmethod
    def _plot_histogram_with_percentiles(
            band_name, band_array, 
            lower:float, upper:float, figsize:tuple,
            out_file:str
        ):
        p_low, p_high = np.percentile(band_array, (lower, upper))
        plt.figure(figsize=figsize)
        plt.hist(band_array.values.ravel(), bins=100, color='gray', alpha=0.7)
        plt.axvline(p_low, color='red', linestyle='--', label=f'{lower}% ({p_low:.1f})')
        plt.axvline(p_high, color='green', linestyle='--', label=f'{upper}% ({p_high:.1f})')
        plt.title(f'{band_name} Histogram with {lower}% and {upper}% Percentiles')
        plt.legend()
        plt.savefig(out_file)


    def plot_histogram_with_percentiles(self, out_dir):
        for name, band in self.bands.items():
            self._plot_histogram_with_percentiles(
                name, band, 
                self.lower_percentile, self.upper_percentile, figsize=(8,4),
                out_file=f"{out_dir}/{name}_{self.lower_percentile}_{self.upper_percentile}.png"
            )
            
        return self