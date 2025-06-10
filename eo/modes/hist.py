import rioxarray
from eo.base_image import BaseImage

def run(**kwargs):
    bn = kwargs.get('bn')
    tif = kwargs.get('tif')
    lo = kwargs.get('lo')
    up = kwargs.get('up')
    out = kwargs.get('out')

    BaseImage._plot_histogram_with_percentiles(
        band_name=bn,
        band_array=rioxarray.open_rasterio(tif),
        lower=int(lo), upper=int(up),
        figsize=(8,4),
        out_file=out
    )