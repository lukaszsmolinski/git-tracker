from uuid import UUID
import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app import models
from app.schemas.collection_schemas import (
    CollectionCreated,
    CollectionCreate,
    Collection,
    CollectionAddRepository,
    CollectionRemoveRepository
)
from app.services import collection_service

security = HTTPBearer(auto_error=False)

router = APIRouter(
    prefix="/collections",
    tags=["collections"],
)


@router.post("", status_code=201, response_model=CollectionCreated)
def create_collection(
    *, db: Session = Depends(get_db), collection_in: CollectionCreate
):
    return collection_service.create(db=db, collection_in=collection_in)


@router.get("/{collection_id}", response_model=Collection)
async def get_collection(
    *, db: Session = Depends(get_db), collection_id: UUID
):
    collection = await collection_service.get_and_update(
        db=db,
        collection_id=collection_id
    )
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found.")
    return collection


@router.post("/{collection_id}/repos", response_model=Collection)
async def add_repository_to_collection(
    *,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    collection_id: UUID,
    collection_in: CollectionAddRepository
):
    collection = await get_collection(db=db, collection_id=collection_id)
    _assert_authorized(collection=collection, credentials=credentials)
    return await collection_service.add_repository(
        db=db,
        collection=collection,
        collection_in=collection_in
    )


@router.delete("/{collection_id}/repos", response_model=Collection)
async def remove_repository_from_collection(
    *,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    collection_id: UUID,
    collection_in: CollectionRemoveRepository
):
    collection = await get_collection(db=db, collection_id=collection_id)
    _assert_authorized(collection=collection, credentials=credentials)
    return collection_service.remove_repository(
        db=db,
        collection=collection,
        collection_in=collection_in
    )


@router.delete("/{collection_id}")
async def delete_collection(
    *,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    collection_id: UUID
):
    collection = await get_collection(db=db, collection_id=collection_id)
    _assert_authorized(collection=collection, credentials=credentials)
    collection_service.delete(
        db=db,
        collection=collection
    )


def _assert_authorized(
    *, 
    collection: models.collection.Collection, 
    credentials: HTTPAuthorizationCredentials
) -> None:
    """Checks if the authorization is valid. 
    
    If it isn't, HTTPException is raised.
    """
    hashed = collection.password
    password = credentials.credentials if credentials is not None else None
    if hashed is not None:
        if not bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8")):
            raise HTTPException(status_code=401, detail="Wrong password.")
