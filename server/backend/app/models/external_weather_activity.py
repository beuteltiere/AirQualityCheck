from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    Column,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import relationship
from app.database.session import Base

class ExternalWeatherActivity(Base):
    __tablename__ = "external_weather_activity"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("external_weather_sources.id"), nullable=False)
    fetched_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    temperature = Column(Float)
    humidity = Column(Float)

    source = relationship("ExternalWeatherSource", back_populates="activity")
    motor_activities = relationship("MotorActivity", back_populates="ext_weather_activity")
