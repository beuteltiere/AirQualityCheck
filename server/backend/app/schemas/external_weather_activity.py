from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class ExternalWeatherActivityBase(BaseModel):
    source_id: int
    temperature: Optional[float] = None
    humidity: Optional[float] = None

class ExternalWeatherActivityCreate(ExternalWeatherActivityBase):
    fetched_at: Optional[datetime] = None

class ExternalWeatherActivityUpdate(BaseModel):
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    fetched_at: Optional[datetime] = None

class ExternalWeatherActivityResponse(ExternalWeatherActivityBase):
    id: int
    fetched_at: datetime

    model_config = {"from_attributes": True}