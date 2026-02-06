from datetime import datetime, timedelta

from sqlalchemy import func

from appointments.models import Appointment, AppointmentStatus
from database.db import SessionLocal


def get_appointments_by_date(date: str):
    """Get all appointments for a specific date."""
    with SessionLocal() as db:
        target_date = datetime.fromisoformat(date).date()
        appointments = (
            db.query(Appointment)
            .filter(func.date(Appointment.date_and_time) == target_date)
            .order_by(Appointment.date_and_time)
            .all()
        )
        return {
            "date": str(target_date),
            "appointments": [
                {
                    "id": str(appt.id),
                    "title": appt.title,
                    "description": appt.description,
                    "date_and_time": appt.date_and_time.isoformat(),
                    "duration": appt.duration,
                    "status": appt.status.value,
                }
                for appt in appointments
            ],
            "total": len(appointments),
        }


def get_appointment_by_title(title: str):
    """Get appointment details by title."""
    with SessionLocal() as db:
        appointment = (
            db.query(Appointment)
            .filter(func.lower(Appointment.title).contains(title.lower()))
            .first()
        )
        if appointment:
            return {
                "id": str(appointment.id),
                "title": appointment.title,
                "description": appointment.description,
                "date_and_time": appointment.date_and_time.isoformat(),
                "duration": appointment.duration,
                "status": appointment.status.value,
            }
        return {"detail": "Appointment not found", "title": title}


def check_time_slot_availability(date_and_time: str, duration: int = 30):
    """Check if a time slot is available."""
    with SessionLocal() as db:
        requested_start = datetime.fromisoformat(date_and_time)
        requested_end = requested_start + timedelta(minutes=duration)

        appointments = (
            db.query(Appointment)
            .filter(Appointment.status == AppointmentStatus.scheduled)
            .all()
        )

        for appt in appointments:
            appt_end = appt.date_and_time + timedelta(minutes=appt.duration)
            if appt.date_and_time < requested_end and appt_end > requested_start:
                return {
                    "available": False,
                    "date_and_time": date_and_time,
                    "duration": duration,
                    "conflict_with": appt.title,
                }

        return {
            "available": True,
            "date_and_time": date_and_time,
            "duration": duration,
        }


def create_new_appointment(
    title: str,
    date_and_time: str,
    duration: int = 30,
    description: str | None = None,
):
    """Create a new appointment."""
    with SessionLocal() as db:
        # Check availability first
        availability = check_time_slot_availability(date_and_time, duration)
        if not availability.get("available"):
            return {
                "detail": "Time slot not available",
                "conflict_with": availability.get("conflict_with"),
            }

        appointment = Appointment(
            title=title,
            description=description,
            date_and_time=datetime.fromisoformat(date_and_time),
            duration=duration,
            status=AppointmentStatus.scheduled,
            created_at=datetime.now(),
        )
        db.add(appointment)
        db.commit()
        db.refresh(appointment)

        return {
            "detail": "Appointment created",
            "appointment": {
                "id": str(appointment.id),
                "title": appointment.title,
                "date_and_time": appointment.date_and_time.isoformat(),
                "duration": appointment.duration,
                "status": appointment.status.value,
            },
        }


def cancel_appointment(title: str):
    """Cancel an appointment by title."""
    with SessionLocal() as db:
        appointment = (
            db.query(Appointment)
            .filter(func.lower(Appointment.title).contains(title.lower()))
            .first()
        )
        if not appointment:
            return {"detail": "Appointment not found", "title": title}

        appointment.status = AppointmentStatus.cancelled
        db.commit()

        return {
            "detail": "Appointment cancelled",
            "title": appointment.title,
            "status": appointment.status.value,
        }
