from typing import List, Optional, Union
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
    relative_orbit: int = Field(alias='sat:relative_orbit')
    instrument_mode: str = Field(alias='sar:instrument_mode')
    polarization: str = Field(alias='s1:polarization')
    preview_image: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
    )
        
class MultiSpectralImage(BaseModel):
    id: str
    acquisition_date: str = Field(alias='datetime')
    cloud_cover: float = Field(alias='eo:cloud_cover')
    proj_epsg: int = Field(alias='proj:epsg')
    gsd: int = Field(alias='gsd')
    preview_image: Optional[str] = None

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
    images_l2a: Optional[List[Union[MultiSpectralImage, None]]] = []
    preview_image: Optional[str] = None
    preview_mask: Optional[str] = None

    def bbox(self):
        return [self.left, self.bottom, self.right, self.top]
    

class S1S2Fusion(BaseModel):
    event_date: str
    name: str
    country: str
    left: float
    bottom: float
    right: float
    top: float
    width: int
    height: int
    s1_image: Optional[SARImage] = None
    s2_image: Optional[MultiSpectralImage] = None
    preview_s1: Optional[str] = None
    preview_s2: Optional[str] = None

    def bbox(self):
        return [self.left, self.bottom, self.right, self.top]
    