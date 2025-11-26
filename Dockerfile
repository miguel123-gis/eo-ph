FROM python:3.11-slim

WORKDIR /eo-ph

COPY requirements.txt .
RUN apt-get update && apt-get install -y \
    # 14.2.0
    gcc \
    g++  \
    # 2.44-3
    binutils \
    # 9.6.0-1
    libproj-dev \
    # 3.10.3
    gdal-bin \
    # 3.10.3+dfsg-1
    libgdal-dev \
    sudo \
    curl \
    lsof \
    vim \
    nginx \
    less \
    procps \
    redis-tools

RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 5001

ENV FLASK_APP=api/routes.py
ENV TZ="Asia/Manila"
ENV PYTHONPATH=/eo-ph

COPY nginx.example /etc/nginx/sites-available/eo-ph