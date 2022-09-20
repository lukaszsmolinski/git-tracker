from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class TrackedRepository(Base):
    __tablename__ = "tracked_repositories"

    repository_id = Column(
        UUID(as_uuid=True), ForeignKey("repositories.id"), primary_key=True
    )
    collection_id = Column(
        UUID(as_uuid=True), ForeignKey("collections.id"), primary_key=True
    )
