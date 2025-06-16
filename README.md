Download a Sentinel-2A/2B image per year
---
### Usage
1. Clone repo
2. Create venv
3. Run `dask-gateway-server` in your terminal
4. Create a `config.yaml` from the sample file
5. Run `python main.py --mode=single` - see sample calls below

#### Sample calls
```
# Get the image with least cloud cover per year from years XX to XX, clip it given the buffer size, and export the annoted images
python main.py --mode=multi --clip --annt

#Export the true color TIF instead
python main.py --mode=multi --clip

# Only get the image with least cloud cover within the entire date range
python main.py --mode=single --clip

# Export all assets (true color and individual bands e.g red, green, blue)
# Cannot be used with --annt
python main.py --mode=single --clip --all
```

#### Configuration
* `bands` - bands to get (will differ per platform e.g. Landsat, Sentinel, etc.)
* `start_date` and `end_date` - date range to search in Sentinel-2 collection
* `latitude` and `longitude` - XY to use to intersect against Sentinel-2 collection
* `buffer_size_meters` - size of circular buffer that will clip the image/raster 
* `export_rgb` - if `True`, will export the individual red, green, and blue bands instead of the true color asset only