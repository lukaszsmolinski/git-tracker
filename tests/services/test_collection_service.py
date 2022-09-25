import uuid
import pytest
from fastapi import HTTPException

from app.enums import Provider
from app.models.collection import Collection
from app.services import collection_service
from app.schemas.collection_schemas import (
    CollectionCreate,
    CollectionAddRepository,
    CollectionRemoveRepository
)


@pytest.mark.parametrize(
    "collection_in, expected",
    [
        [
            CollectionCreate(name="collection1"),
            {"name": "collection1", "protected": False}
        ],
        [
            CollectionCreate(name="collection1", password="123"),
            {"name": "collection1", "protected": True}
        ],
    ]
)
def test_create(db, collection_in, expected):
    cnt = db.query(Collection).count()
    collection = collection_service.create(db=db, collection_in=collection_in)

    assert expected.items() <= collection.__dict__.items()
    assert collection.protected is False or collection.password is not None
    assert db.query(Collection).count() == cnt + 1


@pytest.mark.parametrize(
    "collection_in",
    [
        CollectionCreate(name="collection1"),
        CollectionCreate(name="collection1", password="123")
    ]
)
def test_get_when_collection_exists(db, collection_in):
    c = collection_service.create(db=db, collection_in=collection_in)

    collection = collection_service.get(db=db, collection_id=c.id)

    assert collection.id == c.id
    assert collection.name == collection_in.name
    assert collection.protected == (collection_in.password is not None)


def test_get_when_collection_does_not_exist(db):
    collection = collection_service.get(db=db, collection_id=uuid.uuid4())
    assert collection is None


@pytest.mark.anyio
async def test_get_when_collection_not_empty(db):
    collection = collection_service.create(
        db=db,
        collection_in=CollectionCreate(name="collection1")
    )

    collection_in = CollectionAddRepository(
        repository_name="Hello-World",
        repository_owner="octocat",
        provider=Provider.GITHUB
    )
    collection = await collection_service.add_repository(
        db=db,
        collection=collection,
        collection_in=collection_in
    )

    assert len(collection.repositories) == 1
    assert collection.repositories[0].name == collection_in.repository_name
    assert collection.repositories[0].owner == collection_in.repository_owner
    assert collection.repositories[0].provider == Provider.GITHUB


@pytest.mark.anyio
async def test_add_repository(db):
    collection = collection_service.create(
        db=db,
        collection_in=CollectionCreate(name="collection1")
    )

    collection_in = CollectionAddRepository(
        repository_name="Hello-World",
        repository_owner="octocat",
        provider=Provider.GITHUB
    )
    collection = await collection_service.add_repository(
        db=db,
        collection=collection,
        collection_in=collection_in
    )

    assert len(collection.repositories) == 1
    assert collection.repositories[0].name == collection_in.repository_name
    assert collection.repositories[0].owner == collection_in.repository_owner
    assert collection.repositories[0].provider == collection_in.provider


@pytest.mark.anyio
async def test_add_repository_twice(db):
    collection = collection_service.create(
        db=db,
        collection_in=CollectionCreate(name="collection1")
    )

    collection_in = CollectionAddRepository(
        repository_name="Hello-World",
        repository_owner="octocat",
        provider=Provider.GITHUB
    )
    await collection_service.add_repository(
        db=db,
        collection=collection,
        collection_in=collection_in
    )
    collection = await collection_service.add_repository(
        db=db,
        collection=collection,
        collection_in=collection_in
    )

    assert len(collection.repositories) == 1
    assert collection.repositories[0].name == collection_in.repository_name
    assert collection.repositories[0].owner == collection_in.repository_owner


@pytest.mark.parametrize(
    "collection_in_create, collection_in_add, code",
    [
        [
            CollectionCreate(name="collection1"),
            CollectionAddRepository(
                repository_name="does-not-exist",
                repository_owner="fsjsdfkjdsfadasf",
                provider=Provider.GITHUB
            ),
            404
        ]
    ]
)
@pytest.mark.anyio
async def test_add_repository_fail_with_exception(
    db, collection_in_create, collection_in_add, code
):
    collection = collection_service.create(
        db=db,
        collection_in=collection_in_create
    )

    with pytest.raises(HTTPException) as excinfo:
        await collection_service.add_repository(
            db=db,
            collection=collection,
            collection_in=collection_in_add
        )

    db.refresh(collection)
    assert excinfo.value.status_code == code
    assert len(collection.repositories) == 0


@pytest.mark.anyio
async def test_remove_repository(db):
    collection = collection_service.create(
        db=db,
        collection_in=CollectionCreate(name="collection1")
    )
    collection_in_add = CollectionAddRepository(
        repository_name="Hello-World",
        repository_owner="octocat",
        provider=Provider.GITHUB
    )
    collection = await collection_service.add_repository(
        db=db,
        collection=collection,
        collection_in=collection_in_add
    )

    collection = collection_service.remove_repository(
        db=db,
        collection=collection,
        repository_id=collection.repositories[0].id
    )

    assert len(collection.repositories) == 0


@pytest.mark.parametrize("provider", [Provider.GITHUB, Provider.GITLAB])
def test_remove_repository_that_was_not_added(db, provider):
    collection_in_create = CollectionCreate(name="collection1")
    collection = collection_service.create(
        db=db,
        collection_in=collection_in_create
    )

    with pytest.raises(HTTPException) as excinfo:
        collection_service.remove_repository(
            db=db,
            collection=collection,
            repository_id=uuid.uuid4()
        )

    db.refresh(collection)
    assert excinfo.value.status_code == 404
    assert len(collection.repositories) == 0


def test_delete(db):
    collection_in_create = CollectionCreate(name="collection1")
    collection = collection_service.create(
        db=db,
        collection_in=collection_in_create
    )

    collection_service.delete(
        db=db,
        collection=collection
    )

    collection = collection_service.get(db=db, collection_id=collection.id)
    assert collection is None
