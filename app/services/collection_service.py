from uuid import uuid4, UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import repository_service
from app.models.collection import Collection
from app.models.tracked_repository import TrackedRepository
from app.schemas.collection_schemas import (
    CollectionCreate,
    CollectionAddRepository,
    CollectionRemoveRepository,
    CollectionDelete
)


def create(
    *, db: Session, collection_in: CollectionCreate
) -> Collection:
    """Creates an empty collection."""
    token = str(uuid4()) if collection_in.protected else None
    collection = Collection(**collection_in.dict(), token=token)
    db.add(collection)
    db.commit()
    db.refresh(collection)
    return collection


def get(*, db: Session, collection_id: UUID) -> Collection | None:
    """Returns collection with given id or None if it doesn't exists.

    Returned collection repositories may not be up to date.
    """
    return (
        db.query(Collection)
        .filter(Collection.id == collection_id)
        .one_or_none()
    )


async def update(*, db: Session, collection: Collection) -> None:
    """Updates all repositories belonging to given collection."""
    for repo in collection.repositories:
        await repository_service.update(db=db, repo=repo)


async def get_and_update(
    *, db: Session, collection_id: UUID
) -> Collection | None:
    """Returns collection with given id or None if it doesn't exists.

    Returned collection is up to date.
    """
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
    """Adds repository to collection.

    If the repository doesn't exist or authorization fails, an HTTPException
    is raised. If the repository has already been added to the collection,
    nothing happens.
    """
    _assert_authorized(collection, collection_in.token)

    repository = await repository_service.add(
        db=db,
        name=collection_in.repository_name,
        owner=collection_in.repository_owner,
        provider=collection_in.provider
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
    """Removes repository from collection.

    If the repository doesn't exist, it hasn't been added to the collection
    or authorization fails, an HTTPException is raised.
    """
    _assert_authorized(collection, collection_in.token)

    repository = repository_service.get(
        db=db,
        name=collection_in.repository_name,
        owner=collection_in.repository_owner,
        provider=collection_in.provider
    )
    if repository is None:
        raise HTTPException(
            status_code=404, detail="Tracked repository not found.")

    tracked_repository = (
        db.query(TrackedRepository)
        .filter(TrackedRepository.collection_id == collection.id)
        .filter(TrackedRepository.repository_id == repository.id)
        .one_or_none()
    )
    if tracked_repository is None:
        raise HTTPException(
            status_code=404, detail="Tracked repository not found.")

    db.delete(tracked_repository)
    db.commit()
    db.refresh(collection)

    return collection


def delete(
    *, db: Session, collection: Collection, collection_in: CollectionDelete
) -> None:
    """Deletes coollection.

    If authorization fails, an HTTPException is raised.
    """
    _assert_authorized(collection, collection_in.token)
    db.delete(collection)
    db.commit()


def _assert_authorized(collection: Collection, token: str | None) -> None:
    """Checks if the token is valid for the collection.

    If the token is invalid, an HTTPException is raised.
    """
    if collection.protected and collection.token != token:
        raise HTTPException(status_code=401, detail="Wrong token.")
