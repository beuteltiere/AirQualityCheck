from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.motor_activity import MotorEventType

class MotorActivityBase(BaseModel):
    motor_id: int
    event_type: MotorEventType
    sensor_activity_id: Optional[int] = None
    ext_weather_activity_id: Optional[int] = None

class MotorActivityCreate(MotorActivityBase):
    occurred_at: Optional[datetime] = None

class MotorActivityUpdate(BaseModel):
    event_type: Optional[MotorEventType] = None
    sensor_activity_id: Optional[int] = None
    ext_weather_activity_id: Optional[int] = None
    occurred_at: Optional[datetime] = None

class MotorActivityResponse(MotorActivityBase):
    id: int
    occurred_at: datetime

    model_config = {"from_attributes": True}