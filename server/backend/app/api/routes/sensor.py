from fastapi import APIRouter
from app.database.session import SessionDep
from app.schemas.sensor import SensorCreate, SensorUpdate, SensorResponse
from app.crud import sensor as crud

router = APIRouter()


@router.post("/", response_model=SensorResponse)
def create_sensor(db: SessionDep, sensor: SensorCreate):
    return crud.create_sensor(db=db, sensor=sensor)


@router.put("/{sensor_id}", response_model=SensorResponse)
def update_sensor(db: SessionDep, sensor_id: int, sensor_update: SensorUpdate):
    return crud.update_sensor(db=db, sensor_id=sensor_id, sensor_update=sensor_update)


@router.delete("/{sensor_id}", response_model=SensorResponse)
def delete_sensor(db: SessionDep, sensor_id: int):
    return crud.delete_sensor(db=db, sensor_id=sensor_id)


@router.get("/{sensor_id}", response_model=SensorResponse)
def get_sensor(db: SessionDep, sensor_id: int):
    return crud.get_sensor(db=db, sensor_id=sensor_id)


@router.get("/", response_model=list[SensorResponse])
def get_sensors(db: SessionDep):
    return crud.get_sensors(db=db)