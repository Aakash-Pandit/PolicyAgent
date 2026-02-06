APPOINTMENT_TOOLS = [
    {
        "name": "get_appointments_by_date",
        "description": "Returns all appointments for a specific date.",
        "parameter_definitions": {
            "date": {
                "description": "The date to check in ISO format (YYYY-MM-DD).",
                "type": "str",
                "required": True,
            },
        },
    },
    {
        "name": "get_appointment_by_title",
        "description": "Returns appointment details by searching for the title.",
        "parameter_definitions": {
            "title": {
                "description": "The title or partial title of the appointment.",
                "type": "str",
                "required": True,
            },
        },
    },
    {
        "name": "check_time_slot_availability",
        "description": "Checks if a specific time slot is available for scheduling.",
        "parameter_definitions": {
            "date_and_time": {
                "description": "The date and time to check in ISO format (YYYY-MM-DDTHH:MM:SS).",
                "type": "str",
                "required": True,
            },
            "duration": {
                "description": "Duration in minutes (default 30).",
                "type": "int",
                "required": False,
            },
        },
    },
    {
        "name": "create_new_appointment",
        "description": "Creates a new appointment at the specified time.",
        "parameter_definitions": {
            "title": {
                "description": "The title of the appointment.",
                "type": "str",
                "required": True,
            },
            "date_and_time": {
                "description": "The date and time in ISO format (YYYY-MM-DDTHH:MM:SS).",
                "type": "str",
                "required": True,
            },
            "duration": {
                "description": "Duration in minutes (default 30).",
                "type": "int",
                "required": False,
            },
            "description": {
                "description": "Optional description for the appointment.",
                "type": "str",
                "required": False,
            },
        },
    },
    {
        "name": "cancel_appointment",
        "description": "Cancels an appointment by title.",
        "parameter_definitions": {
            "title": {
                "description": "The title of the appointment to cancel.",
                "type": "str",
                "required": True,
            },
        },
    },
]
