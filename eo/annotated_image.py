import matplotlib.pyplot as plt
import numpy as np
from eo.base_image import BaseImage

class AnnotatedImage:
    def __init__(
            self, 
            base_image: BaseImage,
            lower:float, upper:float, no_data_value:float
        ):
        self.bands = base_image.bands
        self.true_color = base_image.true_color
        self.lower_percentile = lower
        self.upper_percentile = upper
        self.no_data_value = no_data_value

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