import uuid
from sqlalchemy import Column, DateTime, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Collection(Base):
    __tablename__ = "collections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    protected = Column(Boolean)
    password = Column(String, nullable=True)

    repositories = relationship(
        "Repository",
        secondary="tracked_repositories",
        back_populates="collections"
    )
