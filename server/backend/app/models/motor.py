from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    Text,
)
from sqlalchemy.orm import relationship
from app.database.session import Base

class Motor(Base):
    __tablename__ = "motors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)

    activities = relationship("MotorActivity", back_populates="motor", cascade="all, delete-orphan")
