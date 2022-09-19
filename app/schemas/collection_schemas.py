from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

from .repository_schemas import Repository


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
    token: str | None


class CollectionRemoveRepository(BaseModel):
    repository_name: str
    repository_owner: str
    token: str | None


class CollectionDelete(BaseModel):
    token: str | None
