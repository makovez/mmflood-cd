from typing import List
from pydantic import BaseModel

class Config(BaseModel):
    client_id: str
    client_secret: str


class ImageDate(BaseModel):
    start_date: str
    end_date: str

class SARImage(BaseModel):
    id: str
    acquisition_date: str
    orbit_direction: str
    absolute_orbit: int
    relative_orbit:int
    instrument_mode: str
    polarization: str
    preview_image: str

    class Config:
        fields = {
            'acquisition_date': 'datetime',
            'orbit_direction': 'sat:orbit_state',
            'absolute_orbit': 'sat:absolute_orbit',
            'relative_orbit':'sat:relative_orbit',
            'instrument_mode':'sar:instrument_mode',
            'polarization':'s1:polarization',
            }
    

class FloodEvent(BaseModel):
    name: str
    acquisition_date: str
    code: str
    country: str
    event_date: str
    left: float
    bottom: float
    right: float
    top: float
    width: int
    height: int
    images: List[SARImage] = []

    def bbox(self):
        return [self.left, self.bottom, self.right, self.top]

    

