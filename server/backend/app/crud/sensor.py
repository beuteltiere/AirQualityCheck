from app.database.session import SessionDep
from app.models.sensor import Sensor
from app.schemas.sensor import SensorCreate, SensorUpdate


def create_sensor(db: SessionDep, sensor: SensorCreate):
    sensor_data = sensor.model_dump(exclude_unset=True)
    db_sensor = Sensor(**sensor_data)
    db.add(db_sensor)
    db.commit()
    db.refresh(db_sensor)
    return db_sensor


def update_sensor(db: SessionDep, sensor_id: int, sensor_update: SensorUpdate):
    db_sensor = get_sensor(db=db, sensor_id=sensor_id)
    update_data = sensor_update.model_dump(
        exclude_unset=True,
        exclude={"id"},
    )
    for field, value in update_data.items():
        setattr(db_sensor, field, value)
    db.commit()
    db.refresh(db_sensor)
    return db_sensor


def delete_sensor(db: SessionDep, sensor_id: int):
    db_sensor = get_sensor(db=db, sensor_id=sensor_id)
    db.delete(db_sensor)
    db.commit()
    return db_sensor


def get_sensor(db: SessionDep, sensor_id: int):
    return db.query(Sensor).filter(Sensor.id == sensor_id).first()


def get_sensors(db: SessionDep):
    return db.query(Sensor).all()