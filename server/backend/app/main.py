from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database.session import Base, engine
from app.api.main import api_router
from app.models.motor import Motor # noqa: F401
from app.models.motor_activity import MotorActivity # noqa: F401
from app.models.sensor_activity import SensorActivity # noqa: F401
from app.models.sensor import Sensor # noqa: F401
from app.models.external_weather_source import ExternalWeatherSource # noqa: F401
from app.models.external_weather_activity import ExternalWeatherActivity  # noqa: F401

def cstm_generate_unique_id(route: APIRoute) -> str:
  return f"{route.tags[0]}-{route.name}"

app = FastAPI(title=settings.PROJECT_NAME, 
              openapi_url=f"{settings.API_V1_STR}/openapi.json", 
              generate_unique_id_function=cstm_generate_unique_id)

app.include_router(api_router, prefix=settings.API_V1_STR)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)