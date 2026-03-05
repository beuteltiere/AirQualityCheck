from typing import Optional
from pydantic import BaseModel

class SensorBase(BaseModel):
    name: str
    is_active: Optional[bool] = True

class SensorCreate(SensorBase):
    pass

class SensorUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None

class SensorResponse(SensorBase):
    id: int

    model_config = {"from_attributes": True}