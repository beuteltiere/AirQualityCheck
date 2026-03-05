import os
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

database_url = os.getenv("DATABASE_URL")

if database_url:
    engine = create_engine(database_url, pool_pre_ping=True)
else:
    url = URL.create(
        drivername="postgresql+psycopg",
        username="postgres",
        password="postgres",
        host="localhost",
        database="airqualitycheck",
        port=5432,
    )
    engine = create_engine(url, pool_pre_ping=True)

Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()