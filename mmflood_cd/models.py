from typing import List
from pydantic import BaseModel, Field, ConfigDict

class Config(BaseModel):
    client_id: str
    client_secret: str


class ImageDate(BaseModel):
    start_date: str
    end_date: str

class SARImage(BaseModel):
    id: str
    acquisition_date: str = Field(alias='datetime')
    orbit_direction: str = Field(alias='sat:orbit_state')
    absolute_orbit: int = Field(alias='sat:absolute_orbit')
    relative_orbit:int = Field(alias='sat:relative_orbit')
    instrument_mode: str = Field(alias='sar:instrument_mode')
    polarization: str = Field(alias='s1:polarization')
    preview_image: str

    model_config = ConfigDict(
        populate_by_name=True,
    )
        
    

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

    

