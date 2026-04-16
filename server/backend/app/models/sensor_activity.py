from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    Integer,
    DateTime,
    Float,
)
from sqlalchemy.orm import relationship
from app.database.session import Base

class SensorActivity(Base):
    __tablename__ = "sensor_activity"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=False)
    recorded_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    temperature = Column(Float)
    humidity = Column(Float)

    sensor = relationship("Sensor", back_populates="activity")
