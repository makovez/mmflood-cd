# example bbox: [
              #   14.195313963530587,
              #   45.59867608075023,
              #   14.26828125,
              #   45.68935271083946
              # ]

# start date example 2023-10-23T00:00:00Z, enddate example 2023-11-23T23:59:59Z

import os
import yaml, rasterio, tarfile, io, json
import numpy as np
from rasterio.io import MemoryFile
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from typing import List, Union
from mmflood_cd.models import Config, SARImage, FloodEvent, MultiSpectralImage, ImageDate, S1S2Fusion
from mmflood_cd.utils import generate_date_range, today, get_width_height, get_evalscript, refresh_token_on_expire
from PIL import Image

prods_params = {
    'sentinel-1-grd': {
        "processing": {
            "backCoeff": "GAMMA0_TERRAIN",
            "orthorectify": True,
            "demInstance": "MAPZEN"
        },
        "polarization": "DV",
        "acquisitionMode": "IW",
        "resolution": "HIGH"
    },
    'sentinel-2-l2a': {
        "maxCloudCoverage": 40
    }
}

s2la_stats_evalscript =  """
//VERSION=3
function setup() {
  return {
    input: [{
      bands: [
        "CLM",
        "dataMask",
        "SCL"
      ]
    }],
    output: [
      {
        id: "cloud",
        bands: 1
      },
      {
        id: "water",
        bands: 1,
        sampleType: "UINT8"
      },
      {
        id: "dataMask",
        bands: 1
      }]
  }
}


function evaluatePixel(samples) {
    const is_water = (samples.SCL === 6) ? 1 : 0;
    return {
        cloud: [samples.CLM],
        dataMask: [samples.dataMask],
        water: [is_water]
        }
}
"""

class Shub:
    def __init__(self, config_file: str, root_path: str = 'data', fixed_path=None) -> None:
        self.config = self.read_config(config_file)
        self.client_id = self.config.client_id
        self.client_secret = self.config.client_secret
        client = BackendApplicationClient(client_id=self.client_id)
        self.oauth = OAuth2Session(client=client)
        self.directory_path = os.path.join(root_path, today())
        if fixed_path:
            self.directory_path = fixed_path
        os.makedirs(self.directory_path, exist_ok=True)
        self.set_token()

    @refresh_token_on_expire
    def is_processing_units_ok(self):
        url = f"https://services.sentinel-hub.com/api/v1/accounting/usage"
        headers = {"Content-Type": "application/json"}
        response = self.oauth.get(url, headers=headers)
        try:
            requestsOverage = response.json()['requestsOverage']
            processingUnitsOverage = response.json()['processingUnitsOverage']
            is_ok = int(requestsOverage['remaining']) > 200 and int(processingUnitsOverage['remaining']) > 200
        except Exception as e:
            # print(e)
            # print('error on cheking processing unit request')
            return False
        return is_ok

    def read_config(self, file_path: str = 'config.yaml') -> Config:
        with open(file_path, 'r') as file:
            config_data = yaml.safe_load(file)
        return Config(**config_data)

    def set_token(self) -> OAuth2Session:
        # Get token for the session
        token = self.oauth.fetch_token(
            token_url='https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token',
            client_secret=self.client_secret
        )
        print(f"Token: {token}")
        return self.oauth
    
    @refresh_token_on_expire
    def get_image(self, flood_event: Union[FloodEvent, S1S2Fusion], image: Union[SARImage, MultiSpectralImage], prod_type: str = "sentinel-1-grd", 
                  image_date: ImageDate = None, retry = 0):

        if image_date is None:
            image_date = generate_date_range(image.acquisition_date, previous_days=0, max_range_before=1, max_range_after=1)
        
        #width, height = get_width_height(flood_event)
        data = {
            "input": {
                "bounds": {
                    "bbox": flood_event.bbox(),
                    "properties": {
                        "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
                    }
                },
                "data": [
                    {
                        "dataFilter": {
                            "timeRange": {
                                "from": image_date.start_date,
                                "to": image_date.end_date
                            },
                        },
                        **prods_params[prod_type],
                        "type": prod_type
                    }
                ]
            },

            "output": {
                "width": flood_event.width,
                "height": flood_event.height,
                "responses": [
                    {
                        "identifier": "default",
                        "format": {"type": "image/tiff"},
                    }
                ]
            },
            "evalscript": get_evalscript(prod_type)
        }
        
        #url = "https://sh.dataspace.copernicus.eu/api/v1/process" #, "Accept":"application/tar"
        url = "https://services.sentinel-hub.com/api/v1/process"
        response = self.oauth.post(url, headers={"Content-Type": "application/json"}, json=data)

        if len(response.content) < 10000 and retry < 3:
            return self.get_image(flood_event, image, prod_type, retry = retry + 1)
        
        return response.content if len(response.content) > 10000 else None

    def generate_preview(self, data, prod_type):
        if prod_type == "sentinel-1-grd":
            # Read the data and apply 10 * log(x) transformation
            ch1, ch2 = data.read(1), data.read(2)

            # Replace nan values with 0
            ch1[np.isnan(ch1)] = 0
            ch2[np.isnan(ch2)] = 0

            # Stretch images to minmax with 2% and 98% percentile
            ch1_min, ch1_max = np.percentile(ch1, (2, 98))
            ch2_min, ch2_max = np.percentile(ch2, (2, 98))
            
            ch1_stretched = np.clip((ch1 - ch1_min) / (ch1_max - ch1_min + 1e-8), 0, 1)
            ch2_stretched = np.clip((ch2 - ch2_min) / (ch2_max - ch2_min + 1e-8), 0, 1)

            # Convert to 8-bit for saving as JPEG
            ch1_8bit = (ch1_stretched * 255).astype(np.uint8)
            ch2_8bit = (ch2_stretched * 255).astype(np.uint8)

            # Merge the channels into an RGB image
            rgb_image = np.stack([ch1_8bit, ch2_8bit, np.zeros_like(ch1_8bit)], axis=-1)

        elif prod_type == "sentinel-2-l2a":
            ch1 = data.read(1)
            ch1[np.isnan(ch1)] = 0
            ch1_min, ch1_max = np.percentile(ch1, (1, 99))
            ch1_stretched = np.clip((ch1 - ch1_min) / (ch1_max - ch1_min + 1e-8), 0, 1)
            ch1_8bit = (ch1_stretched * 255).astype(np.uint8)
            rgb_image = np.stack([ch1_8bit] * 3, axis=-1)

        else:
            raise ValueError("Invalid product type. Supported types are 'grd' and 'l2a'.")

        return rgb_image

        
    def download_image(self, flood_event: Union[FloodEvent, S1S2Fusion], image: Union[SARImage, MultiSpectralImage], data: Union[bytes, bytearray], prod_type: str = "sentinel-1-grd") -> None:
        # tar = tarfile.open(fileobj=io.BytesIO(data))
        # userdata = json.load(tar.extractfile(tar.getmember('userdata.json')))
        # data = tar.extractfile(tar.getmember('default.tif'))
        # print(len(data))
        os.makedirs(os.path.join(self.directory_path, flood_event.name, 'preview_image'), exist_ok=True)
        with MemoryFile(data) as memfile:
            with memfile.open() as dataset:
                left, bottom, right, top = dataset.bounds
                # print(f"Left: {left}, Bottom: {bottom}, Right: {right}, Top: {top}")

                output_path = os.path.join(self.directory_path, flood_event.name)
                with rasterio.open(os.path.join(output_path, image.id + '.tif'), 'w', **dataset.profile) as dst:
                    dst.write(dataset.read())
                
                rgb_preview = self.generate_preview(dataset, prod_type=prod_type)
                Image.fromarray(rgb_preview).save(os.path.join(output_path, 'preview_image', image.id + '.jpg'))

    def get_stats_l2a(self, flood_event: FloodEvent, th_cloud = 0.1, th_water = 0.01, previous_days=0, max_range_before=360, max_range_after=12) -> Union[None, ImageDate]:
        image_date = generate_date_range(flood_event.event_date, previous_days=previous_days, max_range_before=max_range_before, max_range_after=max_range_after)
        stats_request = {
            "input": {
                "bounds": {
                    "bbox": flood_event.bbox()
                },
                "data": [
                    {
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "mosaickingOrder": "leastRecent"
                        }
                    }
                ]
            },
            "aggregation": {
                "timeRange": {
                    "from": image_date.start_date,
                    "to": image_date.end_date
                },
                "aggregationInterval": {
                    "of": "P1D"
                },
                "evalscript": s2la_stats_evalscript,
                "width": flood_event.width,
                "height": flood_event.height
            }
        }

        url = "https://services.sentinel-hub.com/api/v1/statistics"
        response = self.oauth.post(url, headers={"Content-Type": "application/json"}, json=stats_request)
        stats_json = response.json()
        images_stats = [(data["interval"], data["outputs"]["cloud"]['bands']['B0']['stats']['mean'], data["outputs"]["water"]['bands']['B0']['stats']['mean'] ) for data in stats_json["data"]]
        sorted_data = sorted(images_stats, key=lambda x: x[-1], reverse=True)
        valid_images = []
        for image in sorted_data:
            image_date, cloud, water = image[0], float(image[1]), float(image[2])
            if cloud > th_cloud:
                continue
            elif water > th_water:
                valid_images.append(ImageDate(start_date=image_date['from'], end_date=image_date['to']))

        return valid_images
            