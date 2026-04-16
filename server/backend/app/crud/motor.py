from app.database.session import SessionDep
from app.models.motor import Motor
from app.schemas.motor import MotorCreate, MotorUpdate


def create_motor(db: SessionDep, motor: MotorCreate):
    motor_data = motor.model_dump(exclude_unset=True)
    db_motor = Motor(**motor_data)
    db.add(db_motor)
    db.commit()
    db.refresh(db_motor)
    return db_motor


def update_motor(db: SessionDep, motor_id: int, motor_update: MotorUpdate):
    db_motor = get_motor(db=db, motor_id=motor_id)
    update_data = motor_update.model_dump(
        exclude_unset=True,
        exclude={"id"},
    )
    for field, value in update_data.items():
        setattr(db_motor, field, value)
    db.commit()
    db.refresh(db_motor)
    return db_motor


def delete_motor(db: SessionDep, motor_id: int):
    db_motor = get_motor(db=db, motor_id=motor_id)
    db.delete(db_motor)
    db.commit()
    return db_motor


def get_motor(db: SessionDep, motor_id: int):
    return db.query(Motor).filter(Motor.id == motor_id).first()


def get_motors(db: SessionDep):
    return db.query(Motor).all()