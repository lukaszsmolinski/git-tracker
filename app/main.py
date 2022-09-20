from fastapi import FastAPI

from app.routers import collections
from .database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(collections.router)


@app.get("/status")
async def status():
    return {"message": "OK"}
