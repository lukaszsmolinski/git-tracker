from httpx import AsyncClient
import pytest

from app.main import app
from app.dependencies import get_db
from app.database import engine, SessionLocal, Base
from app.enums import Provider
from app.schemas.collection_schemas import (
    CollectionCreate, 
    CollectionAddRepository
)
from app.services import collection_service


def pytest_sessionstart(session):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def pytest_sessionfinish(session, exitstatus):
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="function")
def db():
    connection = engine.connect()
    connection.begin()
    db = SessionLocal(bind=connection)
    yield db
    db.rollback()
    connection.close()


@pytest.fixture(scope="function")
@pytest.mark.anyio
async def client(db):
    async with AsyncClient(app=app, base_url="http://test") as c:
        app.dependency_overrides[get_db] = lambda: db
        yield c
        app.dependency_overrides = {}


@pytest.fixture(scope="function")
def collection(db):
    return collection_service.create(
        db=db, 
        collection_in=CollectionCreate(name="collection1", password="abc123")
    )


@pytest.fixture(scope="function")
def collection_unprotected(db):
    return collection_service.create(
        db=db, 
        collection_in=CollectionCreate(name="collection1")
    )


@pytest.fixture(scope="function")
@pytest.mark.anyio
async def collection_not_empty(db):
    collection = collection_service.create(
        db=db, 
        collection_in=CollectionCreate(name="collection1", password="abc123")
    )
    collection = await collection_service.add_repository(
        db=db, 
        collection=collection,
        collection_in=CollectionAddRepository(
            repository_name="Hello-World", 
            repository_owner="octocat", 
            provider=Provider.GITHUB
        )
    )
    return await collection_service.add_repository(
        db=db, 
        collection=collection,
        collection_in=CollectionAddRepository(
            repository_name="gitlab", 
            repository_owner="gitlab-org", 
            provider=Provider.GITLAB
        )
    )



@pytest.fixture(scope="function")
@pytest.mark.anyio
async def auth_client(db):
    async with AsyncClient(
        app=app, 
        base_url="http://test", 
        headers={"Authorization": "Bearer abc123"}
    ) as c:
        app.dependency_overrides[get_db] = lambda: db
        yield c
        app.dependency_overrides = {}
