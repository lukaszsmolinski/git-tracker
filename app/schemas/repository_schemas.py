from pydantic import BaseModel
from datetime import datetime

class Repository(BaseModel):
    name: str
    owner: str
    last_commit_at: datetime | None

    class Config:
        orm_mode = True