from fastapi import APIRouter
from app.api.routes import external_weather_source, external_weather_activity

api_router = APIRouter()

api_router.include_router(external_weather_source.router, prefix="/external_weather_source", tags=["external_weather_source"])
api_router.include_router(external_weather_activity.router, prefix="/external_weather_activity", tags=["external_weather_activity"])
