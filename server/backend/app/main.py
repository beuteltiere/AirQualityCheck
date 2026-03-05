from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.middleware.cors import CORSMiddleware

from app.database.session import Base, engine
from app.api.main import api_router

def cstm_generate_unique_id(route: APIRoute) -> str:
  return f"{route.tags[0]}-{route.name}"

app = FastAPI(title="Airqualitycheck API", 
              openapi_url="/api/openapi.json", 
              generate_unique_id_function=cstm_generate_unique_id)

app.include_router(api_router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)