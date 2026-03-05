from sqlalchemy import (
    Column,
    Integer,
    Text,
)
from sqlalchemy.orm import relationship
from app.database.session import Base

class ExternalWeatherSource(Base):
    __tablename__ = "external_weather_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True)
    base_url = Column(Text)

    activity = relationship("ExternalWeatherActivity", back_populates="source", cascade="all, delete-orphan")
