from uuid import uuid4, UUID
import bcrypt
from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import repository_service
from app.models.collection import Collection
from app.models.tracked_repository import TrackedRepository
from app.schemas.collection_schemas import (
    CollectionCreate,
    CollectionAddRepository,
    CollectionRemoveRepository
)


def create(
    *, db: Session, collection_in: CollectionCreate
) -> Collection:
    """Creates an empty collection."""
    hashed = None
    if collection_in.password:
        password = collection_in.password.encode("UTF-8")
        hashed = bcrypt.hashpw(password, bcrypt.gensalt()).decode("UTF-8")

    collection = Collection(
        **collection_in.dict(exclude={"password"}), 
        password=hashed, 
        protected=hashed is not None
    )
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

    If the repository doesn't exist, HTTPException is raised. If 
    the repository has already been added to the collection, nothing happens.
    """
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

    If the repository doesn't exist or it hasn't been added to the collection, 
    an HTTPException is raised.
    """
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


def delete(*, db: Session, collection: Collection) -> None:
    """Deletes coollection."""
    db.delete(collection)
    db.commit()
