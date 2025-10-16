Download a Sentinel-2A/2B image per month/quarter/year 
via Planetary Computer
---
Annotated images (not georeferenced, in PNG) of Payatas, Quezon City from 2015-2025
![payatas](misc/payatas.gif)

True color TIFs of Davao Bypass Road, Davao City from 2015-2025
![payatas](misc/davao.gif)

### Usage
1. Clone repo
2. Create venv
4. Create a `config.yaml` from the sample file
5. Run `docker build -t s2-downloader .` to build image
6. Run to test
```
docker run -it -v $(pwd)/data/processed:/eo-ph/data/processed -p8787:8787 s2-downloader --mode=single --clip
```
7. Check http://localhost:8787/workers to see workers in action



#### Sample arguments
```
# Get the image with least cloud cover per year from years XX to XX, clip it given the buffer size, and export the annoted images
<docker command> --mode=multi --clip --annt

# Plot the municipal boundaries in the output annotated image
<docker command> --mode=multi --clip --annt --bdry

# Export the raster/true color TIF instead
<docker command> --mode=multi --clip

# Get image per quater instead of per year (default)
<docker command> --mode=multi --clip --freq=quarterly

# Only get the image with least cloud cover within the entire date range
<docker command> --mode=single --clip

# Export all assets (true color and individual bands e.g red, green, blue)
# Cannot be used with --annt
<docker command> --mode=single --clip --all
```



#### Configuration
* `bands` - bands to get (will differ per platform e.g. Landsat, Sentinel, etc.)
* `start_date` and `end_date` - date range to search in Sentinel-2 collection
* `latitude` and `longitude` - XY to use to intersect against Sentinel-2 collection
* `buffer_size_meters` - size of circular buffer that will clip the image/raster 