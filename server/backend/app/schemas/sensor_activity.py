from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class SensorActivityBase(BaseModel):
    sensor_id: int
    temperature: Optional[float] = None
    humidity: Optional[float] = None

class SensorActivityCreate(SensorActivityBase):
    recorded_at: Optional[datetime] = None

class SensorActivityUpdate(BaseModel):
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    recorded_at: Optional[datetime] = None

class SensorActivityResponse(SensorActivityBase):
    id: int
    recorded_at: datetime

    model_config = {"from_attributes": True}