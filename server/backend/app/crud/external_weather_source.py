from app.database.session import SessionDep
from app.schemas.external_weather_source import ExternalWeatherSourceCreate, ExternalWeatherSourceUpdate
from app.models.external_weather_source import ExternalWeatherSource

def create_external_weather_source(db: SessionDep, external_weather_source: ExternalWeatherSourceCreate):
    external_weather_source_data = external_weather_source.model_dump(exclude_unset=True)
    db_external_weather_source = ExternalWeatherSource(**external_weather_source_data)
    db.add(db_external_weather_source)
    db.commit()
    db.refresh(db_external_weather_source)
    return db_external_weather_source

def update_external_weather_source(db: SessionDep, external_weather_source_id: int, external_weather_source_update: ExternalWeatherSourceUpdate):
    db_external_weather_source = get_external_weather_source(db=db, external_weather_source_id=external_weather_source_id)
    update_data = external_weather_source_update.model_dump(
        exclude_unset=True,
        exclude={"id"},
    )
    for field, value in update_data.items():
        setattr(db_external_weather_source, field, value)
    db.commit()
    db.refresh(db_external_weather_source)
    return db_external_weather_source

def delete_external_weather_source(db: SessionDep, external_weather_source_id: int):
    db_external_weather_source = get_external_weather_source(db=db, external_weather_source_id=external_weather_source_id)
    db.delete(db_external_weather_source)
    db.commit()
    return db_external_weather_source
    
def get_external_weather_source(db: SessionDep, external_weather_source_id: int):
    external_weather_source = db.query(ExternalWeatherSource).filter(ExternalWeatherSource.id == external_weather_source_id).first()
    return external_weather_source

def get_external_weather_sources(db: SessionDep):
    return db.query(ExternalWeatherSource).all()
