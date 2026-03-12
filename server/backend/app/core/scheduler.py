from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.crud.external_weather_activity import fetch_weather_for_all_sources

scheduler = AsyncIOScheduler()

def start_scheduler():
    scheduler.add_job(
        fetch_weather_for_all_sources,
        trigger=IntervalTrigger(hours=1),
        id="fetch_weather",
        replace_existing=True,
    )
    scheduler.start()