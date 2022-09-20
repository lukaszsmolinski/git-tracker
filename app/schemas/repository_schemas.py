from datetime import datetime
from pydantic import BaseModel

from app.models.repository import Provider


class Repository(BaseModel):
    name: str
    owner: str
    provider: Provider
    last_commit_at: datetime | None

    class Config:
        orm_mode = True
