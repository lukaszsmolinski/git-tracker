from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

from .repository_schemas import Repository
from app.models.repository import Provider


class Collection(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    protected: bool

    class Config:
        orm_mode = True


class CollectionCreated(BaseModel):
    id: UUID
    name: str
    protected: bool

    class Config:
        orm_mode = True


class CollectionCreate(BaseModel):
    name: str
    password: str | None


class CollectionAddRepository(BaseModel):
    repository_name: str
    repository_owner: str
    provider: Provider


class CollectionRemoveRepository(BaseModel):
    repository_name: str
    repository_owner: str
    provider: Provider
