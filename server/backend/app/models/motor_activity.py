from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger,
    Column,
    Enum,
    ForeignKey,
    DateTime,
    Integer
)
from sqlalchemy.orm import relationship
from app.database.session import Base
from enum import Enum as PyEnum

class MotorEventType(PyEnum):
    OPEN = "OPEN"
    CLOSE = "CLOSE"

class MotorActivity(Base):
    __tablename__ = "motor_activity"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    motor_id = Column(Integer, ForeignKey("motors.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(Enum(MotorEventType, name="motor_event_type"), nullable=False)
    occurred_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))

    motor = relationship("Motor", back_populates="activities")
