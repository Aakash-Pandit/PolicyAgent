import uuid
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Enum, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from appointments.choices import AppointmentStatus
from database.db import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    date_and_time = Column(DateTime, nullable=False)
    duration = Column(Integer, nullable=False, default=30)
    status = Column(Enum(AppointmentStatus, name="appointment_status"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AppointmentRequest(BaseModel):
    title: str
    description: str | None = None
    date_and_time: datetime
    duration: int = 30
    status: AppointmentStatus = AppointmentStatus.scheduled


class AppointmentItem(BaseModel):
    id: str
    title: str
    description: str | None = None
    date_and_time: datetime
    duration: int
    status: AppointmentStatus


class AppointmentResponse(BaseModel):
    id: str
    title: str
    description: str | None = None
    date_and_time: datetime
    duration: int
    status: AppointmentStatus


class AppointmentsListResponse(BaseModel):
    appointments: list[AppointmentItem]
    total: int
    message: str
