from fastapi import HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4, UUID

from . import repository_service 
from ..models.collection import Collection
from ..models.tracked_repository import TrackedRepository
from ..schemas.collection_schemas import ( 
    CollectionCreated, 
    CollectionCreate,
    CollectionAddRepository,
    CollectionRemoveRepository,
    CollectionDelete
)


def create(
    *, db: Session, collection_in: CollectionCreate
) -> Collection:
    token = str(uuid4()) if collection_in.protected else None
    collection = Collection(**collection_in.dict(), token=token)
    db.add(collection)
    db.commit()
    db.refresh(collection)
    return collection


def get(*, db: Session, collection_id: UUID) -> Collection | None:
    return (
        db.query(Collection)
        .filter(Collection.id == collection_id)
        .one_or_none()
    )


async def update(*, db: Session, collection: Collection) -> None:
    for repo in collection.repositories:
        await repository_service.update(db=db, repo=repo)


async def get_and_update(
    *, db: Session, collection_id: UUID
) -> Collection | None:
    collection = get(db=db, collection_id=collection_id)
    if collection is not None:
        await update(db=db, collection=collection)
        db.refresh(collection)
    return collection


async def add_repository(
    *,
    db: Session, 
    collection: Collection, 
    collection_in: CollectionAddRepository
) -> Collection:
    _assert_authorized(collection, collection_in.token)

    repository = await repository_service.add(
        db=db,
        name=collection_in.repository_name, 
        owner=collection_in.repository_owner
    )

    is_not_already_tracked = (
        db.query(TrackedRepository)
        .filter(TrackedRepository.collection_id == collection.id)
        .filter(TrackedRepository.repository_id == repository.id)
        .one_or_none() is None
    )
    if is_not_already_tracked:
        tracked_repository = TrackedRepository(
            repository_id=repository.id,
            collection_id=collection.id
        )
        db.add(tracked_repository)
        db.commit()
        db.refresh(collection)

    return collection


def remove_repository(
    *,
    db: Session, 
    collection: Collection, 
    collection_in: CollectionRemoveRepository
) -> Collection:
    _assert_authorized(collection, collection_in.token)

    repository = repository_service.get(
        db=db, 
        name=collection_in.repository_name, 
        owner=collection_in.repository_owner
    )
    if repository is None:
        raise HTTPException(status_code=404, detail="Tracked repository not found.")

    tracked_repository = (
        db.query(TrackedRepository)
        .filter(TrackedRepository.collection_id == collection.id)
        .filter(TrackedRepository.repository_id == repository.id)
        .one_or_none()
    )
    if tracked_repository is None:
        raise HTTPException(status_code=404, detail="Tracked repository not found.")

    db.delete(tracked_repository)
    db.commit()
    db.refresh(collection)

    return collection


def delete(
    *, db: Session, collection: Collection, collection_in: CollectionDelete
) -> None:
    _assert_authorized(collection, collection_in.token)
    db.delete(collection)
    db.commit()


def _assert_authorized(collection: Collection, token: str) -> None:
    if collection.protected and collection.token != token:
        raise HTTPException(status_code=401, detail="Wrong token.")
