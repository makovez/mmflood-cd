# MMFlood-CD

## Scope of Project

The aim of this project is to augment the mmflood dataset by incorporating pre-flood images. The dataset will include the following information for each image:

### 1. Dataset Information

- Bounding Box (BBOX)
- Date of the flood image
- Width and height of the image

### 2. Sentinel-HUB Images Retrieval

The project involves the retrieval of Sentinel-HUB images using an API. The process includes:

- Downloading images from the Sentinel-HUB API
- Storing images in GeoTIFF format
- Capturing pre-image data for specific time ranges:
  - 7 days before the flood
  - 1 month before the flood
  - 3 months before the flood
  - 6 months before the flood
  - 12 months before the flood

### 3. Json with Each Time Series and Post Flood Image

The project will generate a JSON file containing the time series information along with the path and dates of post-flood images.
