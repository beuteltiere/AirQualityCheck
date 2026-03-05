from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    Text,
)
from sqlalchemy.orm import relationship
from app.database.session import Base

class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)

    Activity = relationship("Sensoractivity", back_populates="sensor", cascade="all, delete-orphan")
