import pystac
import rioxarray as rxr
import xarray as xr
import numpy as np
import rasterio 
import zipfile
from osgeo import gdal
from rasterio.plot import plotting_extent
from rasterio.windows import from_bounds
from rasterio.io import MemoryFile
from shapely.geometry import box
from typing import Dict, List, Union, AnyStr
from pathlib import Path

class BaseImage:
    def __init__(
            self, 
            image_item: pystac.Item,
            band_nums: Dict = None,
            true_color = False,
            subset = False,
            **kwargs
        ):
        self.image_item = image_item
        self.band_nums = band_nums
        self.bands = None
        self.true_color = None
        self._extent = None
        self._rgb_stack = None
        self.kwargs = kwargs

        if subset:
            assets = self.kwargs.get("assets")
            bbox = self.kwargs.get("bbox")

            if assets is None or bbox is None:
                raise ValueError("subset=True requires assets and bbox kwargs.")
            
            self.clip(assets=assets, bbox=bbox)

        else:
            if band_nums is not None:
                self.bands = self.get_individual_bands()

            if true_color:
                self.true_color = self.get_visual_asset()


    def get_individual_bands(self) -> Dict:
        """Get the individual bands (e.g. Red, Green, and Blue) from the selected image."""
        assets = self.image_item.assets

        bands = {
            name: rxr.open_rasterio(url.href, chunks=True)
            for name, band_num in self.band_nums.items()
            for band, url in assets.items()
            if band_num == band
        }

        return bands
    

    def get_visual_asset(self) -> xr.DataArray:
        """Get the pre-stacked RGB true color asset from a PySTAC item"""
        va_array = rxr.open_rasterio(self.image_item.assets['visual'].href)

        return va_array
    
    
    def clip(self, assets:list, bbox):
        """Clips the PySTAC item's RGB and visual assets with a shapely box"""
        rgb_assets = list(self.band_nums.keys())
        self.bands = {}

        for name, asset in assets.items():
            cog = self.image_item.assets[asset].href

            with rasterio.open(cog) as src:
                window = from_bounds(*bbox.bounds, transform=src.transform)
                data = src.read(window=window) # Only read the data within the window
                transform = src.window_transform(window)
                crs = src.crs
                count, height, width = data.shape
                coords = {
                    "band": list(range(1, count + 1)),
                    "y": np.arange(height) * transform.e + transform.f,
                    "x": np.arange(width) * transform.a + transform.c
                }
                
                kwargs = src.meta.copy()
                kwargs.update({
                    'height': window.height,
                    'width': window.width,
                    'transform': transform
                })

                # Convert the numpy array to xarray for consistency
                da = xr.DataArray(
                    data,
                    dims=("band", "y", "x"),
                    coords=coords,
                    attrs={
                        "transform": transform,
                        "crs": crs.to_string() if crs else None,
                        "res": src.res,
                        "nodata": src.nodata
                    }
                )

                if name in rgb_assets:
                    self.bands[name] = da
                
                else: 
                    self.true_color = da


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
    

    def process_stack(self, max_val, gamma, type, chunk) -> "BaseImage":
        gamma_corrected = self._rgb_stack ** (1/gamma)
        asuint8 = (gamma_corrected.clip(0,1) * max_val).astype(type)
        ordered = asuint8.assign_coords(band=[1, 2, 3])
        ordered.rio.write_crs(self.bands['red'].rio.crs, inplace=False)
        chunked = ordered.chunk({'band': -1, 'y': chunk, 'x': chunk})
        self._rgb_stack = chunked

        return self
    
    
    @property
    def extent(self) -> box:
        """Extent of the assets: bands and true color"""
        if self._extent is None:
            self._get_image_extent()

        return self._extent
        

    def _get_image_extent(self) -> box:
        """Get extent of the images that is more accurate than :func:`image_utils.get_bbox_from_point`"""
        tc = self.true_color
        extent = plotting_extent(tc[0], transform=tc.rio.transform())
        min_x, max_x, min_y, max_y = extent
        bbox = box(min_x, min_y, max_x, max_y)

        self._extent = bbox

        # TODO Figure out why the output bounds are different from this and get_bbox_from_point using the same point 123.733908, 13.152780
        # (569533.9820448935, 1444152.1070559227, 589533.9820448935, 1464152.1070559227) vs
        # (569538.9820448935, 1444147.1070559227, 589538.9820448935, 1464147.1070559227)

    # TODO Include payload in zip
    def export(self, out_dir, export_rgb=False, to_zip=False, runtime=None):
        out_file = f"{out_dir}/{self.image_item.id}.tif"
        if export_rgb: # Exports Red, Green, Blue, and True Color
            xarrays = {**self.bands, 'true_color': self.true_color}
            for name, xarr in xarrays.items():
                band_out_file = out_file.replace('.tif', f'_{name}.tif')
                if to_zip:
                    out_zip = self.to_zip(
                        raster_xarray=xarr,
                        filename = f"{self.image_item.id}_{name}.tif",
                        out_zip=f"{out_dir}/{runtime}.zip"
                    )
                else:
                    xarr.rio.to_raster(band_out_file, compress="deflate", lock=False, tiled=True)
            
            return out_zip

        else:
            if to_zip:
                out_zip = self.to_zip(
                    raster_xarray=self.true_color,
                    filename = f"{self.image_item.id}.tif",
                    out_zip=f"{out_dir}/{runtime}.zip"
                )
                return out_zip
            else:
                self.true_color.rio.to_raster(out_file, compress="deflate", lock=False, tiled=True)

    @staticmethod
    def memrast_to_s3(raster_xarray, s3_path:str, s3_config:Dict): # TODO This will not work with all since I have to create a URL for each of the object
        gdal.SetConfigOption('AWS_REGION', s3_config.get('AWS_REGION'))
        gdal.SetConfigOption('AWS_SECRET_ACCESS_KEY', s3_config.get('AWS_SECRET_ACCESS_KEY'))
        gdal.SetConfigOption('AWS_ACCESS_KEY_ID', s3_config.get('AWS_ACCESS_KEY_ID'))
        gdal.SetConfigOption('CPL_VSIL_USE_TEMP_FILE_FOR_RANDOM_WRITE', 'YES')

        try:
            with MemoryFile() as memfile:
                raster_xarray.rio.to_raster(memfile.name)
                with memfile.open() as dataset:
                    profile = dataset.profile
                    with rasterio.Env():
                        with rasterio.open(s3_path, 'w', **profile) as dst:
                            dst.write(dataset.read())
        except Exception:
            raise

    @staticmethod
    def to_zip(raster_xarray, filename, out_zip):
        if Path(out_zip).exists:
            mode = 'a'
        else:
            mode = 'w'
        with zipfile.ZipFile(out_zip, mode=mode, compression=zipfile.ZIP_DEFLATED) as zf:
            with MemoryFile() as memfile:
                raster_xarray.rio.to_raster(memfile.name)
                with memfile.open():
                    mem_bytes = memfile.read()
                    zf.writestr(filename, mem_bytes)
        return Path(out_zip).resolve()