import uuid
from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class CachedResponse(Base):
    __tablename__ = "cached_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String)
    json = Column(String, nullable=True)
    etag = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
