from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import yaml, requests
from typing import List
from mmflood_cd.models import Config, FloodEvent, SARImage
from mmflood_cd.utils import generate_date_range

class Catalog:
    def __init__(self, config_file: str) -> None:
        self.config = self.read_config(config_file)
        self.client_id = self.config.client_id
        self.client_secret = self.config.client_secret
        client = BackendApplicationClient(client_id=self.client_id)
        self.oauth = OAuth2Session(client=client)
        self.set_token()

    def read_config(self, file_path: str = 'config.yaml') -> Config:
        with open(file_path, 'r') as file:
            config_data = yaml.safe_load(file)
        return Config(**config_data)

    def set_token(self) -> OAuth2Session:
        # Get token for the session
        token = self.oauth.fetch_token(
            token_url='https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token',
            client_secret=self.client_secret, include_client_id=True
        )
        print(f"Token: {token}")
        return self.oauth
    
    def map_object(self, sar_dict) -> SARImage:
        preview_image = sar_dict['assets']['thumbnail']['href']
        sar_dict.update({'preview_image':preview_image})
        return SARImage(**sar_dict['properties'], **sar_dict)  
    
    def search(self, data: FloodEvent, prod_type: str = "sentinel-1-grd", previous_days=30, max_range=7) -> SARImage:
        
        image_date = generate_date_range(data.acquisition_date, previous_days=previous_days, max_range=max_range)
        data = {
            "bbox": data.bbox(),
            "datetime": f"{image_date.start_date}/{image_date.end_date}",
            "collections": [prod_type],
            "limit": 5,
            "filter": "sar:instrument_mode=\'IW\'"
        }

        url = "https://services.sentinel-hub.com/api/v1/catalog/1.0.0/search"
        headers = {"Content-Type": "application/json"}
        response = self.oauth.post(url, headers=headers, json=data)
        try:
            return self.map_object(response.json()['features'][0])
        except:
            return None
    
    def search_all(self, data: FloodEvent, dates: list) -> List[SARImage]:
        sar_images = []
        for previous_days, max_range in dates:
            img = self.search(data, previous_days=previous_days, max_range=max_range)
            if img: sar_images += [img]

        return sar_images
    

