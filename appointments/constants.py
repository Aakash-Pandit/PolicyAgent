def get_appointment_function_map():
    from appointments.db import (
        cancel_appointment,
        check_time_slot_availability,
        create_new_appointment,
        get_appointment_by_title,
        get_appointments_by_date,
    )

    return {
        "get_appointments_by_date": get_appointments_by_date,
        "get_appointment_by_title": get_appointment_by_title,
        "check_time_slot_availability": check_time_slot_availability,
        "create_new_appointment": create_new_appointment,
        "cancel_appointment": cancel_appointment,
    }
