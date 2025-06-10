import rioxarray
import xarray as xr
from typing import Dict, List, Union, AnyStr
import numpy as np
import matplotlib.pyplot as plt

class BaseImage:
    def __init__(
            self, bands: Dict[str, xr.DataArray], 
            true_color: xr.DataArray,
            lower:float, upper:float, no_data_value:float
        ):
        self.bands = bands
        self.true_color = true_color
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
            
        return self
    
    
    def stretch_contrast(self) -> "BaseImage":
        """Removes the outliers in a band and stretch the remaining values to increase contrast"""
        self.bands = {
            name: self._stretch_contrast(band, self.lower_percentile, self.upper_percentile, self.no_data_value)
            for name, band in self.bands.items()
        }

        return self
    

    def stack_bands(self, band_order:List) -> "BaseImage":
        """Stack individual bands based on order."""
        try:
            bands_to_stack = [self.bands[band] for band in band_order]
        except KeyError as e:
            raise ValueError(f"Band {e} not found in provided bands.") from e
        
        self._rgb_stack = xr.concat(bands_to_stack, dim='band')
        self._rgb_stack['band'] = band_order

        return self
    

    def get_rgb_stack(self, export:Union[bool, AnyStr, None]) -> xr.DataArray:
        if self._rgb_stack is None:
            raise ValueError('No RGB stack. Use stack_bands() first.')
        
        if export:
            self._rgb_stack.rio.to_raster(export, compress="deflate", lock=False, tiled=True)
            return self._rgb_stack
        
        return self._rgb_stack
    

    def get_true_color(self, export:Union[bool, AnyStr, None]) -> xr.DataArray:
        if self.true_color is None:
            raise ValueError('No true color asset. Use image_utils.get_true_color() first.')
        
        if export:
            self.true_color.rio.to_raster(export, compress="deflate", lock=False, tiled=True)
            return self.true_color
        
        return self.true_color
    

    def process_stack(self, max_val, gamma, type, chunk) -> "BaseImage":
        gamma_corrected = self._rgb_stack ** (1/gamma)
        asuint8 = (gamma_corrected.clip(0,1) * max_val).astype(type)
        ordered = asuint8.assign_coords(band=[1, 2, 3])
        ordered.rio.write_crs(self.bands['red'].rio.crs, inplace=False)
        chunked = ordered.chunk({'band': -1, 'y': chunk, 'x': chunk})
        self._rgb_stack = chunked

        return self