import os
import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from database.db import Base

DEFAULT_EMBED_DIM = int(os.getenv("RAG_EMBED_DIM", "1024"))


class PolicyEmbedding(Base):
    __tablename__ = "policy_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    policy_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    document_name = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    embedding = Column(Vector(DEFAULT_EMBED_DIM), nullable=False)
    created = Column(DateTime(timezone=True), server_default=func.now())
