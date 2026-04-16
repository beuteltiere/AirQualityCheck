from fastapi import APIRouter
from app.api.routes import external_weather_source, external_weather_activity, motor, motor_activity, sensor, sensor_activity

api_router = APIRouter()

api_router.include_router(external_weather_source.router, prefix="/external_weather_source", tags=["external_weather_source"])
api_router.include_router(external_weather_activity.router, prefix="/external_weather_activity", tags=["external_weather_activity"])
api_router.include_router(motor.router, prefix="/motor", tags=["motor"])
api_router.include_router(motor_activity.router, prefix="/motor_activity", tags=["motor_activity"])
api_router.include_router(sensor.router, prefix="/sensor", tags=["sensor"])
api_router.include_router(sensor_activity.router, prefix="/sensor_activity", tags=["sensor_activity"])
