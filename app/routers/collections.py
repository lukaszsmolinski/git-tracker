from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from uuid import UUID

from ..dependencies import get_db
from ..services import collection_service as collection_service
from ..schemas.collection_schemas import ( 
    CollectionCreated, 
    CollectionCreate,
    Collection, 
    CollectionAddRepository,
    CollectionRemoveRepository,
    CollectionDelete
)


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


@router.post("/{collection_id}/add", response_model=Collection)
async def add_repository_to_collection(
    *, 
    db: Session = Depends(get_db), 
    collection_id: UUID, 
    collection_in: CollectionAddRepository
):
    collection = await get_collection(db=db, collection_id=collection_id)
    return await collection_service.add_repository(
        db=db, 
        collection=collection, 
        collection_in=collection_in
    )


@router.post("/{collection_id}/remove", response_model=Collection)
async def remove_repository_from_collection(
    *,
    db: Session = Depends(get_db), 
    collection_id: UUID, 
    collection_in: CollectionRemoveRepository
):
    collection = await get_collection(db=db, collection_id=collection_id)
    return collection_service.remove_repository(
        db=db, 
        collection=collection, 
        collection_in=collection_in
    )


@router.delete("/{collection_id}")
async def delete_collection(
    *,
    db: Session = Depends(get_db), 
    collection_id: UUID, 
    collection_in: CollectionDelete
):
    collection = await get_collection(db=db, collection_id=collection_id)
    collection_service.delete(
        db=db, 
        collection=collection, 
        collection_in=collection_in
    )
