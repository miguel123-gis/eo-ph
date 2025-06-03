import xarray as xr
from typing import Dict
import numpy as np

class BaseImage:
    def __init__(self, bands: Dict[str, xr.DataArray]):
        self.bands = bands
        self._rgb_stack = None

    def stretch_contrast(self, lower, upper, nodataval):
        for band_array in self.bands.values():
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