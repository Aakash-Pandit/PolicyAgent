from users.choices import LeaveType, UserType


def test_apply_leave_request(
    client, create_user, create_organization, create_user_organization, auth_headers
):
    user = create_user(username="leave-user", email="leave-user@example.com")
    org = create_organization(name="Leave Test Org")
    create_user_organization(user_id=user.id, organization_id=org.id)

    response = client.post(
        "/leave_requests",
        headers=auth_headers(user),
        json={
            "organization_id": str(org.id),
            "date": "2026-03-20T00:00:00",
            "leave_type": LeaveType.SICK_LEAVE,
            "reason": "Not feeling well",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["leave_type"] == LeaveType.SICK_LEAVE
    assert data["is_accepted"] is False
    assert data["organization_id"] == str(org.id)
    assert data["reason"] == "Not feeling well"


def test_apply_leave_request_not_member(client, create_user, create_organization, auth_headers):
    user = create_user(username="non-member", email="non-member@example.com")
    org = create_organization(name="Another Org")

    response = client.post(
        "/leave_requests",
        headers=auth_headers(user),
        json={
            "organization_id": str(org.id),
            "date": "2026-03-20T00:00:00",
            "leave_type": LeaveType.SICK_LEAVE,
        },
    )
    assert response.status_code == 403
    assert "not an active member" in response.json()["detail"]


def test_apply_duplicate_leave_request(
    client, create_user, create_organization, create_user_organization, auth_headers
):
    user = create_user(username="dup-user", email="dup-user@example.com")
    org = create_organization(name="Dup Org")
    create_user_organization(user_id=user.id, organization_id=org.id)

    # First request
    response1 = client.post(
        "/leave_requests",
        headers=auth_headers(user),
        json={
            "organization_id": str(org.id),
            "date": "2026-03-21T00:00:00",
            "leave_type": LeaveType.SICK_LEAVE,
        },
    )
    assert response1.status_code == 200

    # Duplicate request for same date
    response2 = client.post(
        "/leave_requests",
        headers=auth_headers(user),
        json={
            "organization_id": str(org.id),
            "date": "2026-03-21T00:00:00",
            "leave_type": LeaveType.PRIVILEGE_LEAVE,
        },
    )
    assert response2.status_code == 400
    assert "already have a leave request" in response2.json()["detail"]


def test_get_leave_requests_regular_user(
    client,
    create_user,
    create_organization,
    create_user_organization,
    create_leave_request,
    auth_headers,
):
    org = create_organization(name="List Test Org")
    user1 = create_user(username="user1", email="user1@example.com")
    user2 = create_user(username="user2", email="user2@example.com")
    create_user_organization(user_id=user1.id, organization_id=org.id)
    create_user_organization(user_id=user2.id, organization_id=org.id)

    # Create leave requests for both users
    create_leave_request(user_id=user1.id, organization_id=org.id)
    create_leave_request(user_id=user2.id, organization_id=org.id)

    # User1 should only see their own leave request
    response = client.get("/leave_requests", headers=auth_headers(user1))
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_get_leave_requests_admin_user(
    client,
    create_user,
    create_organization,
    create_user_organization,
    create_leave_request,
    auth_headers,
):
    org = create_organization(name="Admin Test Org")
    admin = create_user(
        username="admin", email="admin@example.com", user_type=UserType.ADMIN
    )
    user = create_user(username="regular", email="regular@example.com")
    create_user_organization(user_id=admin.id, organization_id=org.id)
    create_user_organization(user_id=user.id, organization_id=org.id)

    # Create leave requests for both
    create_leave_request(user_id=admin.id, organization_id=org.id)
    create_leave_request(user_id=user.id, organization_id=org.id)

    # Admin should see all leave requests
    response = client.get("/leave_requests", headers=auth_headers(admin))
    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_get_organization_leave_requests(
    client,
    create_user,
    create_organization,
    create_user_organization,
    create_leave_request,
    auth_headers,
):
    org1 = create_organization(name="Org One")
    org2 = create_organization(name="Org Two")
    admin = create_user(
        username="admin", email="admin@example.com", user_type=UserType.ADMIN
    )
    user = create_user(username="user", email="user@example.com")
    create_user_organization(user_id=user.id, organization_id=org1.id)
    create_user_organization(user_id=user.id, organization_id=org2.id)

    # Create leave requests for different orgs
    create_leave_request(user_id=user.id, organization_id=org1.id)
    create_leave_request(user_id=user.id, organization_id=org2.id)

    # Get leave requests for org1 only
    response = client.get(
        f"/organizations/{org1.id}/leave_requests", headers=auth_headers(admin)
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["leave_requests"][0]["organization_id"] == str(org1.id)


def test_review_accept_leave_request_admin_only(
    client,
    create_user,
    create_organization,
    create_user_organization,
    create_leave_request,
    auth_headers,
):
    org = create_organization(name="Review Test Org")
    admin = create_user(
        username="admin", email="admin@example.com", user_type=UserType.ADMIN
    )
    user = create_user(username="employee", email="employee@example.com")
    create_user_organization(user_id=user.id, organization_id=org.id)

    leave_request = create_leave_request(user_id=user.id, organization_id=org.id)

    # Admin accepts the leave request
    response = client.patch(
        f"/leave_requests/{leave_request.id}/review",
        headers=auth_headers(admin),
        json={"is_accepted": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_accepted"] is True
    assert data["reviewed_by"] == str(admin.id)
    assert data["reviewed_at"] is not None


def test_review_leave_request_non_admin_denied(
    client,
    create_user,
    create_organization,
    create_user_organization,
    create_leave_request,
    auth_headers,
):
    org = create_organization(name="Deny Test Org")
    user = create_user(username="regular", email="regular@example.com")
    create_user_organization(user_id=user.id, organization_id=org.id)

    leave_request = create_leave_request(user_id=user.id, organization_id=org.id)

    # Regular user tries to review - should fail
    response = client.patch(
        f"/leave_requests/{leave_request.id}/review",
        headers=auth_headers(user),
        json={"is_accepted": True},
    )
    assert response.status_code == 403


def test_review_reject_leave_request_admin_only(
    client,
    create_user,
    create_organization,
    create_user_organization,
    create_leave_request,
    auth_headers,
):
    org = create_organization(name="Reject Test Org")
    admin = create_user(
        username="admin", email="admin@example.com", user_type=UserType.ADMIN
    )
    user = create_user(username="employee", email="employee@example.com")
    create_user_organization(user_id=user.id, organization_id=org.id)

    leave_request = create_leave_request(
        user_id=user.id, organization_id=org.id, is_accepted=True
    )

    # Admin rejects the leave request
    response = client.patch(
        f"/leave_requests/{leave_request.id}/review",
        headers=auth_headers(admin),
        json={"is_accepted": False},
    )
    assert response.status_code == 200
    assert response.json()["is_accepted"] is False


def test_delete_own_leave_request(
    client,
    create_user,
    create_organization,
    create_user_organization,
    create_leave_request,
    auth_headers,
):
    org = create_organization(name="Delete Test Org")
    user = create_user(username="user", email="user@example.com")
    create_user_organization(user_id=user.id, organization_id=org.id)

    leave_request = create_leave_request(user_id=user.id, organization_id=org.id)

    response = client.delete(
        f"/leave_requests/{leave_request.id}",
        headers=auth_headers(user),
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Leave request deleted"


def test_delete_other_user_leave_request_denied(
    client,
    create_user,
    create_organization,
    create_user_organization,
    create_leave_request,
    auth_headers,
):
    org = create_organization(name="Delete Deny Org")
    user1 = create_user(username="user1", email="user1@example.com")
    user2 = create_user(username="user2", email="user2@example.com")
    create_user_organization(user_id=user1.id, organization_id=org.id)
    create_user_organization(user_id=user2.id, organization_id=org.id)

    leave_request = create_leave_request(user_id=user1.id, organization_id=org.id)

    # User2 tries to delete User1's leave request - should fail
    response = client.delete(
        f"/leave_requests/{leave_request.id}",
        headers=auth_headers(user2),
    )
    assert response.status_code == 403


def test_admin_can_delete_any_leave_request(
    client,
    create_user,
    create_organization,
    create_user_organization,
    create_leave_request,
    auth_headers,
):
    org = create_organization(name="Admin Delete Org")
    admin = create_user(
        username="admin", email="admin@example.com", user_type=UserType.ADMIN
    )
    user = create_user(username="employee", email="employee@example.com")
    create_user_organization(user_id=user.id, organization_id=org.id)

    leave_request = create_leave_request(user_id=user.id, organization_id=org.id)

    # Admin can delete any user's leave request
    response = client.delete(
        f"/leave_requests/{leave_request.id}",
        headers=auth_headers(admin),
    )
    assert response.status_code == 200


def test_get_single_leave_request(
    client,
    create_user,
    create_organization,
    create_user_organization,
    create_leave_request,
    auth_headers,
):
    org = create_organization(name="Single Test Org")
    user = create_user(username="user", email="user@example.com")
    create_user_organization(user_id=user.id, organization_id=org.id)

    leave_request = create_leave_request(user_id=user.id, organization_id=org.id)

    response = client.get(
        f"/leave_requests/{leave_request.id}",
        headers=auth_headers(user),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(leave_request.id)
    assert data["organization_id"] == str(org.id)
    assert data["organization_name"] == org.name


def test_leave_request_not_found(client, create_user, auth_headers):
    user = create_user(username="user", email="user@example.com")

    response = client.get(
        "/leave_requests/00000000-0000-0000-0000-000000000000",
        headers=auth_headers(user),
    )
    assert response.status_code == 404


def test_delete_leave_request_not_found(client, create_user, auth_headers):
    user = create_user(username="user", email="user@example.com")

    response = client.delete(
        "/leave_requests/00000000-0000-0000-0000-000000000000",
        headers=auth_headers(user),
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Leave request not found"
