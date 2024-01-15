# MMFlood-CD

The aim of this project is to augment the mmflood dataset by incorporating pre-flood images.

A demo of the dataset is available to view here: https://optuna.cokyc.it

## Set up and run the project
1. Create an account in sentinel hub and register an oauth client to get credentials from https://apps.sentinel-hub.com/dashboard
2. Copy config_example.yaml to config.yaml and update with your oauth credentials
```
client_secret: <secret>
client_id: <client id>
```
3. Run main.py to download the images from the api, using metadata.json which contains same flood events of MMFlood dataset

### Notes
All the images are without speckle filtering applied, with orthorectification (with MAPZEN Dem) and with gamma0 ellipsoid as backscatter. You can learn more on the GRD product type from https://docs.sentinel-hub.com/api/latest/data/sentinel-1-grd/

You can play with requests builder to learn more about the different parameters https://apps.sentinel-hub.com/requests-builder/

## Folder structure example
Each event has a folder with an unique name (same naming style of mmflood dataset). Each event folder has tif images, each with VV,VH channels and a preview_image folder containing jpg images with VV attached to RED and VH attached to green channel.

There will be also a json named flood_events.json with details of each flood event retrieved from sentinel-hub.
```
EMSR
  > EMSR470-0-16
    > preview_image
      -> S1A..XXXX.jpg
      -> S1B..XXXX.jpg
      -> S1B..XXXX.jpg 
    -> S1A..XXXX.tif
    -> S1B..XXXX.tif
    -> S1B..XXXX.tif
  > EMSR284-2-3
    > preview_image
      -> S1A..XXXX.jpg
      -> S1A..XXXX.jpg
      -> S1B..XXXX.jpg
      -> S1B..XXXX.jpg
    -> S1A..XXXX.tif
    -> S1A..XXXX.tif
    -> S1B..XXXX.tif
    -> S1B..XXXX.tif
 -> flood_events.json
```

### Dataset Information -> flood_events.json 

- Bounding Box
- Date of the flood image
- Width and height of the image (Same from MMFLOOD)
- EMSR code
- Preview Image
- Preview Mask
- Images List (List of images pre-flood)

### Sentinel-HUB Images Retrieval

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


### Web page to view the images and explore dataset
The dataset containts in the main page informations about the flood event with the preview image generated from mmflood dataset directly.

![Main-Page](https://github.com/makovez/mmflood-cd/assets/21694707/8b52a864-48b6-47fc-9e21-d3d855d944d9)

When an event is clicked a modal is opened with the information about the specific EMSR event. The first two red boxes images contains respecively the mmflood image and the mmflood mask. The other images range from 0-6 (where available). Where 0 refers to the image after the flood event retrieved via sentinel-api (which should be similar to the mmflood image), the others are previous images from the most to the least recent.

![flood-event](https://github.com/makovez/mmflood-cd/assets/21694707/14ec1dcb-24d5-48c4-9b2c-f1c669bd2727)
