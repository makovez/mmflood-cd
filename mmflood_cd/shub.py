# example bbox: [
              #   14.195313963530587,
              #   45.59867608075023,
              #   14.26828125,
              #   45.68935271083946
              # ]

# start date example 2023-10-23T00:00:00Z, enddate example 2023-11-23T23:59:59Z

import requests, os
import yaml, rasterio, tarfile, io, json
from rasterio.io import MemoryFile
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from typing import List, Union
from mmflood_cd.models import Config, SARImage, FloodEvent
from mmflood_cd.utils import generate_date_range, today, get_width_height, get_evalscript

class Shub:
    def __init__(self, config_file: str, root_path: str = 'data') -> None:
        self.config = self.read_config(config_file)
        self.client_id = self.config.client_id
        self.client_secret = self.config.client_secret
        client = BackendApplicationClient(client_id=self.client_id)
        self.oauth = OAuth2Session(client=client)
        self.directory_path = os.path.join(root_path, today())

        os.makedirs(self.directory_path)
        self.set_token()

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
    
    def get_image(self, flood_event: FloodEvent, data: SARImage, prod_type: str = "sentinel-1-grd", retry = 0) -> requests.Response:
        image_date = generate_date_range(data.acquisition_date, previous_days=0, max_range=1)
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
            return self.get_image(flood_event, data, prod_type, retry = retry + 1)
        
        return response.content if len(response.content) > 10000 else None

    def download_image(self, flood_event: FloodEvent, image: SARImage, data: Union[bytes, bytearray]) -> None:
        # tar = tarfile.open(fileobj=io.BytesIO(data))
        # userdata = json.load(tar.extractfile(tar.getmember('userdata.json')))
        # data = tar.extractfile(tar.getmember('default.tif'))
        print(len(data))
        os.makedirs(os.path.join(self.directory_path, flood_event.name), exist_ok=True)
        with MemoryFile(data) as memfile:
            with memfile.open() as dataset:
                left, bottom, right, top = dataset.bounds
                print(f"Left: {left}, Bottom: {bottom}, Right: {right}, Top: {top}")

                output_file_path = os.path.join(self.directory_path, flood_event.name, image.id + '.tif')
                with rasterio.open(output_file_path, 'w', **dataset.profile) as dst:
                    dst.write(dataset.read())

                print(f"GeoTIFF saved to {output_file_path}")
    