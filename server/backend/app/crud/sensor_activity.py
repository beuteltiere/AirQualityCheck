from datetime import datetime
from sqlalchemy.orm import Session
from app.models.sensor_activity import SensorActivity

def get_by_date_range(
    db: Session,
    start: datetime,
    end: datetime,
    sensor_id: int | None = None,
) -> list[SensorActivity]:
    query = db.query(SensorActivity).filter(
        SensorActivity.recorded_at >= start,
        SensorActivity.recorded_at <= end,
    )
    if sensor_id:
        query = query.filter(SensorActivity.sensor_id == sensor_id)

    return query.order_by(SensorActivity.recorded_at).all()