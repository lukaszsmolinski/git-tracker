from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database

from app.config import settings


SQLALCHEMY_DATABASE_URL = (
    "postgresql://"
    f"{settings.postgres_user}:{settings.postgres_password}@"
    f"{settings.postgres_server}:{settings.postgres_port}/"
    f"{settings.postgres_db}"
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)
if not database_exists(engine.url):
    create_database(engine.url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
