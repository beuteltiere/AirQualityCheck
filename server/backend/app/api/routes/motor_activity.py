from datetime import datetime
from fastapi import APIRouter
from app.database.session import SessionDep
from app.models.motor_activity import MotorEventType
from app.crud.motor_activity import get_by_date_range

router = APIRouter()

@router.get("/")
def get_motor_activity(
    db: SessionDep,
    start: datetime,
    end: datetime,
    motor_id: int | None = None,
    event_type: MotorEventType | None = None,
):
    return get_by_date_range(db, start, end, motor_id, event_type)