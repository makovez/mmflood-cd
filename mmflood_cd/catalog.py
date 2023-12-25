from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import yaml, requests
from mmflood_cd.models import Config, GeoData
from mmflood_cd.utils import generate_date_range, today, get_width_height, get_evalscript

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
    
    def search(self, data: GeoData, prod_type: str = "sentinel-1-grd", previous_days=30, max_range=7) -> requests.Response:
        
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

        return response.json()
    

