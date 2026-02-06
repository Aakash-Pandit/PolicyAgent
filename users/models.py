import uuid
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Column, Date, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from database.db import Base
from users.choices import UserType


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
    created_at = Column(DateTime(timezone=True), server_default=func.now())


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
