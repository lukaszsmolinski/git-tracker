from fastapi import FastAPI

from .database import engine, Base
from app.routers import collections

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(collections.router)

@app.get("/status")
async def status():
    return {"message": "OK"}
