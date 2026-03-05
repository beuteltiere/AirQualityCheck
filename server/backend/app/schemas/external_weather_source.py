from typing import Optional
from pydantic import BaseModel

class ExternalWeatherSourceBase(BaseModel):
    name: str
    base_url: Optional[str] = None

class ExternalWeatherSourceCreate(ExternalWeatherSourceBase):
    pass

class ExternalWeatherSourceUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None

class ExternalWeatherSourceResponse(ExternalWeatherSourceBase):
    id: int

    model_config = {"from_attributes": True}