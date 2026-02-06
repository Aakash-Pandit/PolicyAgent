def test_appointments_crud(client, create_user, auth_headers):
    user = create_user(username="appt-user", email="appt-user@example.com")

    create_response = client.post(
        "/appointments",
        headers=auth_headers(user),
        json={
            "title": "Team Meeting",
            "description": "Weekly sync",
            "date_and_time": "2026-01-30T10:00:00",
            "duration": 30,
            "status": "scheduled",
        },
    )
    assert create_response.status_code == 200
    appointment_id = create_response.json()["id"]

    list_response = client.get("/appointments", headers=auth_headers(user))
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    get_response = client.get(
        f"/appointments/{appointment_id}", headers=auth_headers(user)
    )
    assert get_response.status_code == 200
    assert get_response.json()["id"] == appointment_id
    assert get_response.json()["title"] == "Team Meeting"

    delete_response = client.delete(
        f"/appointments/{appointment_id}", headers=auth_headers(user)
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Appointment deleted"


def test_appointment_not_found(client, create_user, auth_headers):
    user = create_user(username="appt-user", email="appt-user@example.com")
    response = client.get(
        "/appointments/00000000-0000-0000-0000-000000000000",
        headers=auth_headers(user),
    )
    assert response.status_code == 404
