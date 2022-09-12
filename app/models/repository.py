from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..database import Base

class Repository(Base):
    __tablename__ = "repositories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    owner = Column(String)
    last_commit_at = Column(DateTime, nullable=True)

    collections = relationship(
        "Collection", 
        secondary="tracked_repositories", 
        back_populates="repositories"
    )
