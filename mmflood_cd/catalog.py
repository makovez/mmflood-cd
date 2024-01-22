from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import yaml, requests
from typing import List
from mmflood_cd.models import Config, FloodEvent, SARImage
from mmflood_cd.utils import generate_date_range, refresh_token_on_expire

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
        return SARImage(**sar_dict['properties'], **sar_dict)  
    
    @refresh_token_on_expire
    def search(self, data: FloodEvent, prod_type: str = "sentinel-1-grd", previous_days=30, max_range_before=7, max_range_after=7, relative_orbit = None, most_recent = True) -> SARImage:
        
        image_date = generate_date_range(data.event_date, previous_days=previous_days, max_range_before=max_range_before, max_range_after=max_range_after)
        data = {
            "bbox": data.bbox(),
            "datetime": f"{image_date.start_date}/{image_date.end_date}",
            "collections": [prod_type],
            "limit": 100,
            "filter": "sar:instrument_mode=\'IW\'"
        }

        url = "https://services.sentinel-hub.com/api/v1/catalog/1.0.0/search"
        headers = {"Content-Type": "application/json"}
        response = self.oauth.post(url, headers=headers, json=data)

        # priority to orbit rather then time preference
        if relative_orbit:
            for image in response.json()['features']:
                if image['properties']['sat:relative_orbit'] == relative_orbit:
                    return self.map_object(image) # get orbit preference

        time_preference = 0 if most_recent else -1
        try:
            return self.map_object(response.json()['features'][time_preference]) # most recent
        except Exception as e:
            print(e)
            print(response.text)
            return None
        
    
    def search_all(self, data: FloodEvent, dates: list) -> List[SARImage]:
        sar_images = []
        relative_orbit = None
        most_recent = False
        for ranges in dates:
            previous_days = ranges[0]
            max_range_before, max_range_after = ranges[1], ranges[1]
            if len(ranges) > 2:
                max_range_before = ranges[1]
                max_range_after = ranges[2]
            
            # If first iteration (relative orbit None means first iteration) then select the more far image (because more near the flood event)
            if relative_orbit is None: 
                most_recent = False
            
            img = self.search(data, previous_days=previous_days, max_range_before=max_range_before, max_range_after=max_range_after, relative_orbit=relative_orbit, most_recent=most_recent)
            if img:
                if relative_orbit is None: relative_orbit = img.relative_orbit # set orbit preference
                sar_images += [img]

        return sar_images
    

