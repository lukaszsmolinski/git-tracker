from httpx import AsyncClient
import pytest

from app.main import app
from app.dependencies import get_db
from app.database import engine, SessionLocal, Base


@pytest.fixture
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


def pytest_sessionstart(session):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def pytest_sessionfinish(session, exitstatus):
    Base.metadata.drop_all(bind=engine)
