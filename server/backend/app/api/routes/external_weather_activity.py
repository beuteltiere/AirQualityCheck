from fastapi import APIRouter
from datetime import datetime
from app.database.session import SessionDep
from app.crud.external_weather_activity import get_by_date_range

router = APIRouter()

@router.get("/")
def get_weather_activity(db: SessionDep, start: datetime, end: datetime, source_id: int | None = None):
    return get_by_date_range(db, start, end, source_id)