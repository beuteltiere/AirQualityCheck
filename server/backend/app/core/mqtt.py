import json
from datetime import datetime, timezone
from aiomqtt import Client
from app.database.session import SessionLocal
from app.models.sensor_activity import SensorActivity
from app.models.sensor import Sensor
from app.models.motor_activity import MotorActivity, MotorEventType
from app.models.motor import Motor

MQTT_HOST = "172.31.183.207"
MQTT_TOPIC = "home/sensor/#"
MOTOR_TOPIC_PREFIX = "home/sensor/motor"
MOTOR_COMMAND_TOPIC_PREFIX = "home/sensor/motor/command"

_buffer: dict = {}

async def start_mqtt():
    print("MQTT: connecting to broker...")
    async with Client(MQTT_HOST) as client:
        await client.subscribe("home/sensor/#")
        await client.subscribe("home/sensor/motor")
        await client.subscribe("home/sensor/motor/#")
        print("MQTT: subscribed to home/sensor/# and home/sensor/motor/#")
        async for message in client.messages:
            topic = str(message.topic)
            print(f"MQTT: received {topic} = {message.payload.decode()}")
            if topic == MOTOR_TOPIC_PREFIX or topic.startswith(f"{MOTOR_TOPIC_PREFIX}/"):
                await handle_motor_message(message)
            else:
                await handle_message(message)

async def handle_message(message):
    topic = str(message.topic)
    payload = message.payload.decode()
    field = topic.split("/")[-1]

    if field == "temperature":
        _buffer["temperature"] = float(payload)
    elif field == "humidity":
        _buffer["humidity"] = float(payload)

    if "temperature" in _buffer and "humidity" in _buffer:
        db = SessionLocal()
        try:
            sensor = db.query(Sensor).filter_by(is_active=True).first()
            if sensor:
                activity = SensorActivity(
                    sensor_id=sensor.id,
                    recorded_at=datetime.now(timezone.utc),
                    temperature=_buffer.pop("temperature"),
                    humidity=_buffer.pop("humidity"),
                )
                db.add(activity)
                db.commit()
                print(f"MQTT: inserted sensor_activity for sensor {sensor.id} — temp={activity.temperature}, humidity={activity.humidity}")
            else:
                print("MQTT: no active sensor found in DB, skipping insert")
        finally:
            db.close()

STATUS_MAP = {
    "stopped": MotorEventType.CLOSE,
    "running": MotorEventType.OPEN,
}


def get_motor_for_activity(db):
    motor = db.query(Motor).filter_by(is_active=True).first()
    if motor:
        return motor

    return db.query(Motor).order_by(Motor.id).first()


def get_last_motor_event(db, motor_id: int):
    return (
        db.query(MotorActivity)
        .filter(MotorActivity.motor_id == motor_id)
        .order_by(MotorActivity.occurred_at.desc(), MotorActivity.id.desc())
        .first()
    )

async def handle_motor_message(message):
    payload = message.payload.decode().strip().lower()
    event_type = STATUS_MAP.get(payload)

    if not event_type:
        print(f"MQTT motor: unknown status '{payload}', skipping")
        return

    db = SessionLocal()
    try:
        motor = get_motor_for_activity(db)
        if motor:
            last_event = get_last_motor_event(db, motor.id)
            if last_event and last_event.event_type == event_type:
                print(
                    f"MQTT motor: status for motor {motor.id} already {event_type.value}, skipping duplicate"
                )
                return

            activity = MotorActivity(
                motor_id=motor.id,
                event_type=event_type,
                occurred_at=datetime.now(timezone.utc),
            )
            db.add(activity)
            db.commit()
            print(f"MQTT motor: inserted motor_activity for motor {motor.id} — event={event_type.value}")
        else:
            print("MQTT motor: no motor found in DB, skipping insert")
    finally:
        db.close()


async def publish_motor_command(degrees: int):
    topic = MOTOR_COMMAND_TOPIC_PREFIX
    payload = f"rotate:{degrees}"
    async with Client(MQTT_HOST) as client:
        await client.publish(topic, payload)
    print(f"MQTT motor: published command {topic} payload={payload}")