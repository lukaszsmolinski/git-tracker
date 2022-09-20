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
    repositories: list[Repository]

    class Config:
        orm_mode = True


class CollectionCreate(BaseModel):
    name: str
    protected: bool


class CollectionCreated(BaseModel):
    id: UUID
    name: str
    protected: bool
    token: str | None

    class Config:
        orm_mode = True


class CollectionAddRepository(BaseModel):
    repository_name: str
    repository_owner: str
    provider: Provider
    token: str | None


class CollectionRemoveRepository(BaseModel):
    repository_name: str
    repository_owner: str
    provider: Provider
    token: str | None


class CollectionDelete(BaseModel):
    token: str | None
