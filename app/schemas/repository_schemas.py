from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

from app.enums import Provider


class Repository(BaseModel):
    id: UUID
    name: str
    owner: str
    provider: Provider
    last_commit_at: datetime | None

    class Config:
        orm_mode = True
