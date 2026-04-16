from fastapi import APIRouter
from app.database.session import SessionDep
from app.schemas.motor import MotorCreate, MotorUpdate, MotorResponse
from app.crud import motor as crud
from app.core.mqtt import publish_motor_command

router = APIRouter()


@router.post("/", response_model=MotorResponse)
def create_motor(db: SessionDep, motor: MotorCreate):
    return crud.create_motor(db=db, motor=motor)


@router.put("/{motor_id}", response_model=MotorResponse)
def update_motor(db: SessionDep, motor_id: int, motor_update: MotorUpdate):
    return crud.update_motor(db=db, motor_id=motor_id, motor_update=motor_update)


@router.delete("/{motor_id}", response_model=MotorResponse)
def delete_motor(db: SessionDep, motor_id: int):
    return crud.delete_motor(db=db, motor_id=motor_id)


@router.get("/{motor_id}", response_model=MotorResponse)
def get_motor(db: SessionDep, motor_id: int):
    return crud.get_motor(db=db, motor_id=motor_id)


@router.get("/", response_model=list[MotorResponse])
def get_motors(db: SessionDep):
    return crud.get_motors(db=db)


@router.post("/command/360")
async def publish_motor_command_360():
    await publish_motor_command(360)
    return {"topic": "home/sensor/motor/command", "payload": {"rotate": 360}}


@router.post("/command/-360")
async def publish_motor_command_minus_360():
    await publish_motor_command(-360)
    return {"topic": "home/sensor/motor/command", "payload": {"rotate": -360}}