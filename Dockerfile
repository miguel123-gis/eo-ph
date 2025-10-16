FROM python:3.11-slim

WORKDIR /eo-ph

COPY requirements.txt .
RUN apt-get update && apt-get install -y gcc g++  binutils libproj-dev gdal-bin libgdal-dev
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENTRYPOINT ["python", "-m", "eo"]

