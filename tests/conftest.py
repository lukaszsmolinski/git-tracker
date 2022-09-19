import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_db
from app.database import engine, SessionLocal, Base


@pytest.fixture(scope="function")
def db():
    connection = engine.connect()
    transaction = connection.begin()
    db = SessionLocal(bind=connection)
    yield db
    db.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db):
    with TestClient(app) as c:
        app.dependency_overrides[get_db] = lambda: db
        yield c
        app.dependency_overrides = {}


def pytest_sessionstart(session):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def pytest_sessionfinish(session, exitstatus):
    Base.metadata.drop_all(bind=engine)
