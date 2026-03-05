from typing import Optional
from pydantic import BaseModel

class MotorBase(BaseModel):
    name: str
    is_active: Optional[bool] = True

class MotorCreate(MotorBase):
    pass

class MotorUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None

class MotorResponse(MotorBase):
    id: int

    model_config = {"from_attributes": True}