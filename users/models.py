import uuid
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.db import Base
from users.choices import LeaveType, UserType


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    username = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    user_type = Column(
        Enum(UserType, name="user_type"), nullable=False, default=UserType.REGULAR
    )
    date_of_birth = Column(Date, nullable=False)
    created = Column(DateTime(timezone=True), server_default=func.now())
    modified = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to leave requests
    leave_requests = relationship("LeaveRequest", foreign_keys="LeaveRequest.user_id", back_populates="user", cascade="all, delete-orphan")


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    date = Column(Date, nullable=False)
    leave_type = Column(
        Enum(LeaveType, name="leave_type"), nullable=False
    )
    reason = Column(Text, nullable=True)
    is_accepted = Column(Boolean, default=False)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    created = Column(DateTime(timezone=True), server_default=func.now())
    modified = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="leave_requests")
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class UserRequest(BaseModel):
    first_name: str
    last_name: str
    username: str
    password: str
    email: str
    phone: str
    gender: str
    user_type: UserType = UserType.REGULAR
    date_of_birth: datetime


class UserItem(BaseModel):
    id: str
    first_name: str
    last_name: str
    username: str
    email: str
    phone: str
    gender: str
    user_type: UserType
    date_of_birth: datetime


class UserResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    username: str
    email: str
    phone: str
    gender: str
    user_type: UserType
    date_of_birth: datetime


class UsersListResponse(BaseModel):
    users: list[UserItem]
    total: int
    message: str


# Pydantic Models - LeaveRequest
class LeaveRequestCreate(BaseModel):
    organization_id: str
    date: datetime
    leave_type: LeaveType
    reason: str | None = None


class LeaveRequestItem(BaseModel):
    id: str
    user_id: str
    username: str | None = None
    organization_id: str
    organization_name: str | None = None
    date: datetime
    leave_type: LeaveType
    reason: str | None = None
    is_accepted: bool
    reviewed_by: str | None = None
    reviewer_name: str | None = None
    reviewed_at: datetime | None = None
    applied_at: datetime | None = None
    created: datetime | None = None


class LeaveRequestResponse(BaseModel):
    id: str
    user_id: str
    organization_id: str
    date: datetime
    leave_type: LeaveType
    reason: str | None = None
    is_accepted: bool
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    applied_at: datetime | None = None
    created: datetime | None = None


class LeaveRequestsListResponse(BaseModel):
    leave_requests: list[LeaveRequestItem]
    total: int
    message: str


class LeaveRequestReview(BaseModel):
    is_accepted: bool
