import xarray as xr
from typing import Dict
import numpy as np
import matplotlib.pyplot as plt

class BaseImage:
    def __init__(
            self, bands: Dict[str, xr.DataArray], 
            lower:float, upper:float, no_data_value:float
        ):
        self.bands = bands
        self._rgb_stack = None
        self.lower_percentile = lower
        self.upper_percentile = upper
        self.no_data_value = no_data_value


    @staticmethod
    def _stretch_contrast(band_array, lower, upper, nodataval) -> xr.DataArray:
        # Pre-filter the band
        band_array = band_array.astype(np.float32)
        masked_array = band_array.where(band_array != nodataval)

        # Get the value at the XX% (low) and XX% (high) percentile
        p_low_da = masked_array.quantile(lower / 100.0, skipna=True)
        p_high_da = masked_array.quantile(upper / 100.0, skipna=True)
        p_low = float(p_low_da)
        p_high = float(p_high_da)

        # Stretch and clip the band
        stretched = (band_array - p_low) / (p_high - p_low)
        return stretched.clip(0,1)
    

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


    def plot_histogram_with_percentiles(self):
        for name, band in self.bands.items():
            self._plot_histogram_with_percentiles(
                name, band, 
                self.lower_percentile, self.upper_percentile, figsize=(8,4),
                out_file=f"data/misc/{name}_{self.lower_percentile}_{self.upper_percentile}.png"
                )
    
    
    def stretch_contrast(self) -> Dict:
        """Removes the outliers in a band and stretch the remaining values to increase contrast"""
        stretched = {
            name: self._stretch_contrast(band, self.lower_percentile, self.upper_percentile, self.no_data_value)
            for name, band in self.bands.items()
        }

        return stretched