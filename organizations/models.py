import uuid
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.db import Base


# SQLAlchemy Models
class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    address = Column(String(500), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to policies
    policies = relationship("Policy", back_populates="organization", cascade="all, delete-orphan")


class Policy(Base):
    __tablename__ = "policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    max_leave_days = Column(Integer, nullable=False, default=20)
    carry_forward_days = Column(Integer, nullable=False, default=5)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to organization
    organization = relationship("Organization", back_populates="policies")


# Pydantic Models - Organization
class OrganizationRequest(BaseModel):
    name: str
    description: str | None = None
    address: str | None = None
    email: str | None = None
    phone: str | None = None
    is_active: bool = True


class OrganizationItem(BaseModel):
    id: str
    name: str
    description: str | None = None
    address: str | None = None
    email: str | None = None
    phone: str | None = None
    is_active: bool
    created_at: datetime | None = None


class OrganizationResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    address: str | None = None
    email: str | None = None
    phone: str | None = None
    is_active: bool


class OrganizationsListResponse(BaseModel):
    organizations: list[OrganizationItem]
    total: int
    message: str


# Pydantic Models - Policy
class PolicyRequest(BaseModel):
    organization_id: str
    name: str
    description: str | None = None
    max_leave_days: int = 20
    carry_forward_days: int = 5
    is_active: bool = True


class PolicyItem(BaseModel):
    id: str
    organization_id: str
    organization_name: str | None = None
    name: str
    description: str | None = None
    max_leave_days: int
    carry_forward_days: int
    is_active: bool
    created_at: datetime | None = None


class PolicyResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    description: str | None = None
    max_leave_days: int
    carry_forward_days: int
    is_active: bool


class PoliciesListResponse(BaseModel):
    policies: list[PolicyItem]
    total: int
    message: str
