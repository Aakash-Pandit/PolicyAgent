import uuid
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, String, Text
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
    created = Column(DateTime(timezone=True), server_default=func.now())
    modified = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    policies = relationship("Policy", back_populates="organization", cascade="all, delete-orphan")
    members = relationship("UserOrganization", back_populates="organization", cascade="all, delete-orphan")


class Policy(Base):
    __tablename__ = "policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    document_name = Column(String(255), nullable=True)
    file = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created = Column(DateTime(timezone=True), server_default=func.now())
    modified = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to organization
    organization = relationship("Organization", back_populates="policies")


class UserOrganization(Base):
    __tablename__ = "user_organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    joined_date = Column(Date, nullable=False)
    left_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    created = Column(DateTime(timezone=True), server_default=func.now())
    modified = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="members")


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
    created: datetime | None = None


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
    is_active: bool = True


class PolicyItem(BaseModel):
    id: str
    organization_id: str
    organization_name: str | None = None
    name: str
    description: str | None = None
    document_name: str | None = None
    file_path: str | None = None
    is_active: bool
    created: datetime | None = None


class PolicyResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    description: str | None = None
    document_name: str | None = None
    file_path: str | None = None
    is_active: bool


class PoliciesListResponse(BaseModel):
    policies: list[PolicyItem]
    total: int
    message: str


# Pydantic Models - UserOrganization
class UserOrganizationRequest(BaseModel):
    user_id: str
    organization_id: str
    joined_date: datetime
    left_date: datetime | None = None
    is_active: bool = True


class UserOrganizationUpdate(BaseModel):
    joined_date: datetime | None = None
    left_date: datetime | None = None
    is_active: bool | None = None


class UserOrganizationItem(BaseModel):
    id: str
    user_id: str
    username: str | None = None
    organization_id: str
    organization_name: str | None = None
    joined_date: datetime
    left_date: datetime | None = None
    is_active: bool
    created: datetime | None = None


class UserOrganizationResponse(BaseModel):
    id: str
    user_id: str
    organization_id: str
    joined_date: datetime
    left_date: datetime | None = None
    is_active: bool


class UserOrganizationsListResponse(BaseModel):
    memberships: list[UserOrganizationItem]
    total: int
    message: str
