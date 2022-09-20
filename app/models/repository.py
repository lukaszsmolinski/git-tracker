import enum
import uuid
from sqlalchemy import Column, DateTime, String, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Provider(str, enum.Enum):
    GITHUB = "github"
    GITLAB = "gitlab"


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    owner = Column(String)
    provider = Column(Enum(Provider))
    last_commit_at = Column(DateTime, nullable=True)

    collections = relationship(
        "Collection",
        secondary="tracked_repositories",
        back_populates="repositories"
    )
