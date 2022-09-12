from sqlalchemy import Column, DateTime, String, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..database import Base


class Collection(Base):
    __tablename__ = "collections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    protected = Column(Boolean)
    token = Column(String, nullable=True)

    repositories = relationship(
        "Repository", 
        secondary="tracked_repositories", 
        back_populates="collections"
    )
