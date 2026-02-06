from datetime import datetime

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from application.app import app
from appointments.models import (
    Appointment,
    AppointmentItem,
    AppointmentRequest,
    AppointmentResponse,
    AppointmentsListResponse,
)
from database.db import drop_appointments_table, get_db


@app.get("/appointments", response_model=AppointmentsListResponse)
async def get_appointments(db: Session = Depends(get_db)):
    rows = db.query(Appointment).order_by(Appointment.created_at.desc()).all()
    appointments = [
        AppointmentItem(
            id=str(row.id),
            title=row.title,
            description=row.description,
            date_and_time=row.date_and_time,
            duration=row.duration,
            status=row.status,
        )
        for row in rows
    ]
    total = len(appointments)
    message = "No appointments found" if total == 0 else "Appointments retrieved"
    return AppointmentsListResponse(
        appointments=appointments,
        total=total,
        message=message,
    )


@app.get("/appointments/{appointment_id}", response_model=AppointmentItem)
async def get_appointment(appointment_id: str, db: Session = Depends(get_db)):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    return AppointmentItem(
        id=str(appointment.id),
        title=appointment.title,
        description=appointment.description,
        date_and_time=appointment.date_and_time,
        duration=appointment.duration,
        status=appointment.status,
    )


@app.post("/appointments", response_model=AppointmentResponse)
async def create_appointment(
    appointment: AppointmentRequest, db: Session = Depends(get_db)
):
    new_appointment = Appointment(
        title=appointment.title,
        description=appointment.description,
        date_and_time=appointment.date_and_time,
        duration=appointment.duration,
        status=appointment.status,
        created_at=datetime.now(),
    )
    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)

    return AppointmentResponse(
        id=str(new_appointment.id),
        title=new_appointment.title,
        description=new_appointment.description,
        date_and_time=new_appointment.date_and_time,
        duration=new_appointment.duration,
        status=new_appointment.status,
    )


@app.delete("/appointments/{appointment_id}")
async def delete_appointment(appointment_id: str, db: Session = Depends(get_db)):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    db.delete(appointment)
    db.commit()

    return {"status": "ok", "message": "Appointment deleted"}


@app.delete("/admin/drop-appointments-db")
async def drop_appointments_db_table():
    drop_appointments_table()
    return {"status": "ok", "message": "Appointments database table dropped"}
