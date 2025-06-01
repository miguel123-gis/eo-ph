import pystac_client
import planetary_computer
import geopandas
import rioxarray
import xarray as xr
from dask_gateway import Gateway
from dask.distributed import Client, LocalCluster, Lock
import numpy as np
from rioxarray.merge import merge_arrays
import matplotlib.pyplot as plt
from rasterio.enums import ColorInterp


# Set up dask
gateway = Gateway("http://127.0.0.1:8000")
gateway.list_clusters()

# Create a cluster
cluster = gateway.new_cluster()
cluster.scale(4)

# Autoscale the clusters
client = cluster.get_client()
cluster.adapt(minimum=4, maximum=50)

class BaseImage:
    def __init__(self, start_date, end_date, lat, lon, collection):
        self.start_date = start_date
        self.end_date = end_date
        self.lat = lat
        self.lon = lon
        self.collection = collection


    def search_collection(self):
        pass

    def get_image(self):
        pass

    def get_rgb_bands(self):
        pass

    def convert_to_arrays(self):
        pass

    def stretch_contrast(self):
        pass

    def stack_rgb_arrays(self):
        pass

    def post_process(self):
        pass

    def export_to_tif(self):
        pass



