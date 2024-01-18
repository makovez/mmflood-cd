# example bbox: [
              #   14.195313963530587,
              #   45.59867608075023,
              #   14.26828125,
              #   45.68935271083946
              # ]

# start date example 2023-10-23T00:00:00Z, enddate example 2023-11-23T23:59:59Z

import requests, os
import yaml, rasterio, tarfile, io, json
import numpy as np
from rasterio.io import MemoryFile
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from typing import List, Union
from mmflood_cd.models import Config, SARImage, FloodEvent
from mmflood_cd.utils import generate_date_range, today, get_width_height, get_evalscript
from PIL import Image

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

    def is_processing_units_ok(self) -> bool:
        url = f"https://services.sentinel-hub.com/api/v1/accounting/usage"
        headers = {"Content-Type": "application/json"}
        response = self.oauth.get(url, headers=headers)
        try:
            requestsOverage = response.json()['requestsOverage']
            processingUnitsOverage = response.json()['processingUnitsOverage']
            is_ok = int(requestsOverage['remaining']) > 200 and int(processingUnitsOverage['remaining']) > 200
        except Exception as e:
            print(e)
            print('error on cheking processing unit request')
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
    
    def get_image(self, flood_event: FloodEvent, sar_image: SARImage, prod_type: str = "sentinel-1-grd", retry = 0) -> requests.Response:
        image_date = generate_date_range(sar_image.acquisition_date, previous_days=0, max_range_before=1, max_range_after=1)
        #width, height = get_width_height(flood_event)
        data = {
            "input": {
                "bounds": {
                    "bbox": flood_event.bbox()
                },
                "data": [
                    {
                        "dataFilter": {
                            "timeRange": {
                                "from": image_date.start_date,
                                "to": image_date.end_date
                            },
                            "processing": {
                                "backCoeff": "GAMMA0_TERRAIN",
                                "orthorectify": True,
                                "demInstance": "MAPZEN"
                            },
                            "polarization": "DV",
                            "acquisitionMode": "IW",
                            "resolution": "HIGH"
                        },
                        
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
                    },
                    {
                        "identifier": "userdata",
                        "format": {"type": "application/json"},
                    }
                ]
            },
            "evalscript": get_evalscript()
        }
        
        #url = "https://sh.dataspace.copernicus.eu/api/v1/process" #, "Accept":"application/tar"
        url = "https://services.sentinel-hub.com/api/v1/process"
        response = self.oauth.post(url, headers={"Content-Type": "application/json"}, json=data)

        if len(response.content) < 10000 and retry < 3:
            return self.get_image(flood_event, sar_image, prod_type, retry = retry + 1)
        
        return response.content if len(response.content) > 10000 else None

    def generate_preview(self, data):
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

        return rgb_image
        
    def download_image(self, flood_event: FloodEvent, image: SARImage, data: Union[bytes, bytearray]) -> None:
        # tar = tarfile.open(fileobj=io.BytesIO(data))
        # userdata = json.load(tar.extractfile(tar.getmember('userdata.json')))
        # data = tar.extractfile(tar.getmember('default.tif'))
        print(len(data))
        os.makedirs(os.path.join(self.directory_path, flood_event.name, 'preview_image'), exist_ok=True)
        with MemoryFile(data) as memfile:
            with memfile.open() as dataset:
                left, bottom, right, top = dataset.bounds
                print(f"Left: {left}, Bottom: {bottom}, Right: {right}, Top: {top}")

                output_path = os.path.join(self.directory_path, flood_event.name)
                with rasterio.open(os.path.join(output_path, image.id + '.tif'), 'w', **dataset.profile) as dst:
                    dst.write(dataset.read())
                
                rgb_preview = self.generate_preview(dataset)
                Image.fromarray(rgb_preview).save(os.path.join(output_path, 'preview_image', image.id + '.jpg'))

    