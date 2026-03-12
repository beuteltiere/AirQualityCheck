import httpx
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database.session import SessionDep
from app.models.external_weather_activity import ExternalWeatherActivity
from app.models.external_weather_source import ExternalWeatherSource
from app.database.session import SessionLocal

async def fetch_weather_for_all_sources():
    db: Session = SessionLocal()
    try:
        sources = db.query(ExternalWeatherSource).all()
        async with httpx.AsyncClient() as client:
            for source in sources:
                try:
                    params = {
                        "latitude": 47.21717,
                        "longitude": 15.62297,
                        "current": "temperature_2m,relative_humidity_2m",
                        "forecast_days": 1,
                    }
                    resp = await client.get(f"{source.base_url}/forecast", params=params)
                    resp.raise_for_status()
                    data = resp.json()
                    current = data["current"]

                    activity = ExternalWeatherActivity(
                        source_id=source.id,
                        fetched_at=datetime.now(timezone.utc),
                        temperature=current["temperature_2m"],
                        humidity=current["relative_humidity_2m"],
                    )
                    db.add(activity)
                except Exception as e:
                    print(f"Failed to fetch from source {source.id}: {e}")
        db.commit()
    finally:
        db.close()

def get_by_date_range(db: SessionDep, start: datetime, end: datetime, source_id: int | None = None) -> list[ExternalWeatherActivity]:
    query = db.query(ExternalWeatherActivity).filter(
        ExternalWeatherActivity.fetched_at >= start,
        ExternalWeatherActivity.fetched_at <= end,
    )
    if source_id:
        query = query.filter(ExternalWeatherActivity.source_id == source_id)
    return query.order_by(ExternalWeatherActivity.fetched_at).all()