# MMFlood-CD



## Scope of Project

The aim of this project is to augment the mmflood dataset by incorporating pre-flood images. The dataset will include the following information for each image:

### 1. Dataset Information

- Bounding Box
- Date of the flood image
- Width and height of the image (Same from MMFLOOD)
- EMSR code
- Preview Image
- Preview Mask
- Images List (List of images pre-flood)

### 2. Sentinel-HUB Images Retrieval

The project involves the retrieval of Sentinel-HUB images using their API. The process includes:

- Downloading images from the Sentinel-HUB API
- Storing images in GeoTIFF format
- Converting images from GeoTIFF to jpg to generated preview
- Capturing pre-image data for specific time ranges:
  - 7 days before the flood
  - 1 month before the flood
  - 3 months before the flood
  - 6 months before the flood
  - 12 months before the flood

### 3. Json with Each Time Series and Post Flood Image

The project will generate a JSON file containing the time series information along with the path and dates of post-flood images.

### 4. Web page to view the images and explore dataset

![Main-Page](https://github.com/makovez/mmflood-cd/assets/21694707/8b52a864-48b6-47fc-9e21-d3d855d944d9)

![flood-event](https://github.com/makovez/mmflood-cd/assets/21694707/14ec1dcb-24d5-48c4-9b2c-f1c669bd2727)
