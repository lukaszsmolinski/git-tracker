import pytest
import uuid
from fastapi import HTTPException

from app.services import collection_service
from app.schemas.collection_schemas import ( 
    CollectionCreate,
    CollectionAddRepository,
    CollectionRemoveRepository,
    CollectionDelete
)


@pytest.mark.parametrize(
    "collection_in, expected",
    [
        [
            CollectionCreate(name="collection1", protected=False), 
            {"name": "collection1", "protected": False}
        ],
        [
            CollectionCreate(name="collection1", protected=True), 
            {"name": "collection1", "protected": True}
        ],
    ]
)
def test_create(db, collection_in, expected):
    collection = collection_service.create(db=db, collection_in=collection_in)

    assert expected.items() <= collection.__dict__.items()
    assert collection.protected is False or collection.token is not None


@pytest.mark.parametrize(
    "collection_in",
    [
        CollectionCreate(name="collection1", protected=False),
        CollectionCreate(name="collection1", protected=True)
    ]
)
def test_get_when_collection_exists(db, collection_in):
    c = collection_service.create(db=db, collection_in=collection_in)

    collection = collection_service.get(db=db, collection_id=c.id)

    assert collection.id == c.id
    assert collection_in.__dict__.items() <= collection.__dict__.items()


def test_get_when_collection_does_not_exist(db):
    collection = collection_service.get(db=db, collection_id=uuid.uuid4())
    assert collection is None


@pytest.mark.asyncio
async def test_add_repository(db):
    collection = collection_service.create(
        db=db, 
        collection_in=CollectionCreate(name="collection1", protected=False)
    )

    collection_in = CollectionAddRepository(
        repository_name="Hello-World", 
        repository_owner="octocat",
        provider="github"
    )
    collection = await collection_service.add_repository(
        db=db, 
        collection=collection, 
        collection_in=collection_in
    )

    assert len(collection.repositories) == 1
    assert collection.repositories[0].name == "Hello-World"
    assert collection.repositories[0].owner == "octocat"


@pytest.mark.asyncio
async def test_add_repository_using_correct_token(db):
    collection = collection_service.create(
        db=db, 
        collection_in=CollectionCreate(name="collection1", protected=True)
    )

    collection_in = CollectionAddRepository(
        repository_name="Hello-World", 
        repository_owner="octocat",
        provider="github",
        token=collection.token
    )
    collection = await collection_service.add_repository(
        db=db, 
        collection=collection, 
        collection_in=collection_in
    )

    assert len(collection.repositories) == 1
    assert collection.repositories[0].name == "Hello-World"
    assert collection.repositories[0].owner == "octocat"


@pytest.mark.asyncio
async def test_add_repository_twice(db):
    collection = collection_service.create(
        db=db, 
        collection_in=CollectionCreate(name="collection1", protected=False)
    )

    collection_in = CollectionAddRepository(
        repository_name="Hello-World", 
        repository_owner="octocat",
        provider="github"
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
    assert collection.repositories[0].name == "Hello-World"
    assert collection.repositories[0].owner == "octocat"


@pytest.mark.parametrize(
    "collection_in_create, collection_in_add, code",
    [
        [
            CollectionCreate(name="collection1", protected=False), 
            CollectionAddRepository(
                repository_name="does-not-exist", 
                repository_owner="fsjsdfkjdsfadasf",
                provider="github"
            ),
            404
        ],
        [
            CollectionCreate(name="collection1", protected=True), 
            CollectionAddRepository(
                repository_name="Hello-World", 
                repository_owner="octocat",
                provider="github",
                token=None
            ),
            401
        ],
        [
            CollectionCreate(name="collection1", protected=True), 
            CollectionAddRepository(
                repository_name="Hello-World", 
                repository_owner="octocat",
                provider="github",
                token=str(uuid.uuid4())
            ),
            401
        ],
    ]
)
@pytest.mark.asyncio
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


@pytest.mark.asyncio
async def test_remove_repository(db):
    collection = collection_service.create(
        db=db, 
        collection_in=CollectionCreate(name="collection1", protected=False)
    )
    collection_in_add = CollectionAddRepository(
        repository_name="Hello-World", 
        repository_owner="octocat",
        provider="github"
    )
    collection = await collection_service.add_repository(
        db=db, 
        collection=collection, 
        collection_in=collection_in_add
    )

    collection_in_remove = CollectionRemoveRepository(**collection_in_add.dict())
    collection = collection_service.remove_repository(
        db=db,
        collection=collection,
        collection_in=collection_in_remove
    )

    assert len(collection.repositories) == 0


@pytest.mark.asyncio
async def test_remove_repository_using_wrong_token(db):
    collection_in_create = CollectionCreate(name="collection1", protected=True)
    collection = collection_service.create(
        db=db, 
        collection_in=collection_in_create
    )
    collection_in_add = CollectionAddRepository(
        repository_name="Hello-World", 
        repository_owner="octocat",
        provider="github",
        token=collection.token
    )
    collection = await collection_service.add_repository(
        db=db, 
        collection=collection, 
        collection_in=collection_in_add
    )

    collection_in_remove = CollectionRemoveRepository(**collection_in_add.dict())
    collection_in_remove.token = str(uuid.uuid4())
    with pytest.raises(HTTPException) as excinfo:
        collection_service.remove_repository(
            db=db, 
            collection=collection, 
            collection_in=collection_in_remove
        )

    db.refresh(collection)
    assert excinfo.value.status_code == 401
    assert len(collection.repositories) == 1


def test_remove_repository_that_was_not_added(db):
    collection_in_create = CollectionCreate(name="collection1", protected=False)
    collection = collection_service.create(
        db=db, 
        collection_in=collection_in_create
    )

    collection_in_remove = CollectionRemoveRepository(
        repository_name="Hello-World", 
        repository_owner="octocat",
        provider="github"
    )
    with pytest.raises(HTTPException) as excinfo:
        collection_service.remove_repository(
            db=db, 
            collection=collection, 
            collection_in=collection_in_remove
        )

    db.refresh(collection)
    assert excinfo.value.status_code == 404
    assert len(collection.repositories) == 0



def test_delete(db):
    collection_in_create = CollectionCreate(name="collection1", protected=False)
    collection = collection_service.create(
        db=db, 
        collection_in=collection_in_create
    )

    collection_service.delete(
        db=db, 
        collection=collection, 
        collection_in=CollectionDelete()
    )

    collection = collection_service.get(db=db, collection_id=collection.id)
    assert collection is None


def test_delete_using_correct_token(db):
    collection_in_create = CollectionCreate(name="collection1", protected=True)
    collection = collection_service.create(
        db=db, 
        collection_in=collection_in_create
    )

    collection_service.delete(
        db=db, 
        collection=collection, 
        collection_in=CollectionDelete(token=collection.token)
    )

    collection = collection_service.get(db=db, collection_id=collection.id)
    assert collection is None


@pytest.mark.parametrize(
    "collection_in_delete",
    [
        CollectionDelete(token=None),
        CollectionDelete(token=str(uuid.uuid4()))
    ]
)
def test_delete_fail_with_exception(db, collection_in_delete):
    collection_in_create = CollectionCreate(name="collection1", protected=True)
    collection = collection_service.create(
        db=db, 
        collection_in=collection_in_create
    )

    with pytest.raises(HTTPException) as excinfo:
        collection_service.delete(
            db=db, 
            collection=collection, 
            collection_in=collection_in_delete
        )

    collection = collection_service.get(db=db, collection_id=collection.id)
    assert collection is not None
    assert excinfo.value.status_code == 401
