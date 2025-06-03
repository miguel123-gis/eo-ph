import xarray as xr
from typing import Dict
import numpy as np

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
    def plot_histogram_with_percentiles(band_array):
        pass
    
    
    def stretch_contrast(self) -> Dict:
        """Removes the outliers in a band and stretch the remaining values to increase contrast"""
        stretched = {
            name: self._stretch_contrast(band, self.lower_percentile, self.upper_percentile, self.no_data_value)
            for name, band in self.bands.items()
        }

        return stretched
    