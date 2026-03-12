from fastapi import APIRouter
from app.database.session import SessionDep
from app.schemas.external_weather_source import ExternalWeatherSourceCreate, ExternalWeatherSourceUpdate, ExternalWeatherSourceResponse
from app.crud import external_weather_source as crud

router = APIRouter()

@router.post("/external_weather_sources/", response_model=ExternalWeatherSourceResponse)
def create_external_weather_source(db: SessionDep, external_weather_source: ExternalWeatherSourceCreate):
    external_weather_source = crud.create_external_weather_source(db=db, external_weather_source=external_weather_source)
    return external_weather_source

@router.put("/{external_weather_source_id}", response_model=ExternalWeatherSourceResponse)
def update_external_weather_source(db: SessionDep, external_weather_source_id: int, external_weather_source_update: ExternalWeatherSourceUpdate):
    external_weather_source = crud.update_external_weather_source(db=db, external_weather_source_id=external_weather_source_id, external_weather_source_update=external_weather_source_update)
    return external_weather_source

@router.delete("/{external_weather_source_id}", response_model=ExternalWeatherSourceResponse)
def delete_external_weather_source(external_weather_source_id: int, db: SessionDep):
    external_weather_source = crud.delete_external_weather_source(db=db, external_weather_source_id=external_weather_source_id)
    return external_weather_source

@router.get("/{external_weather_source_id}", response_model=ExternalWeatherSourceResponse)
def get_external_weather_source(external_weather_source_id: int, db: SessionDep):
    external_weather_source = crud.get_external_weather_source(db=db, external_weather_source_id=external_weather_source_id)
    return external_weather_source

@router.get("/", response_model=list[ExternalWeatherSourceResponse])
def get_external_weather_sources(db: SessionDep):
    external_weather_sources = crud.get_external_weather_sources(db=db)
    return external_weather_sources