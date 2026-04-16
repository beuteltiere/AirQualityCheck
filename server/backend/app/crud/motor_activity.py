from datetime import datetime
from sqlalchemy.orm import Session
from app.models.motor_activity import MotorActivity, MotorEventType

def get_by_date_range(
    db: Session,
    start: datetime,
    end: datetime,
    motor_id: int | None = None,
    event_type: MotorEventType | None = None,
) -> list[MotorActivity]:
    query = db.query(MotorActivity).filter(
        MotorActivity.occurred_at >= start,
        MotorActivity.occurred_at <= end,
    )
    if motor_id:
        query = query.filter(MotorActivity.motor_id == motor_id)
    if event_type:
        query = query.filter(MotorActivity.event_type == event_type)

    return query.order_by(MotorActivity.occurred_at).all()