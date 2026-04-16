from datetime import datetime
from fastapi import APIRouter
from app.database.session import SessionDep
from app.crud.sensor_activity import get_by_date_range

router = APIRouter()

@router.get("/")
def get_sensor_activity(
    db: SessionDep,
    start: datetime,
    end: datetime,
    sensor_id: int | None = None,
):
    return get_by_date_range(db, start, end, sensor_id)