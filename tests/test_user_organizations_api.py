def test_join_organization(client, create_user, create_organization, auth_headers):
    user = create_user(username="member", email="member@example.com")
    org = create_organization(name="Test Company")

    response = client.post(
        "/user-organizations",
        headers=auth_headers(user),
        json={
            "user_id": str(user.id),
            "organization_id": str(org.id),
            "joined_date": "2026-01-15T00:00:00",
            "is_active": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == str(user.id)
    assert data["organization_id"] == str(org.id)
    assert data["is_active"] is True


def test_cannot_join_same_organization_twice(
    client, create_user, create_organization, create_user_organization, auth_headers
):
    user = create_user(username="member", email="member@example.com")
    org = create_organization(name="Test Company")
    create_user_organization(user_id=user.id, organization_id=org.id)

    response = client.post(
        "/user-organizations",
        headers=auth_headers(user),
        json={
            "user_id": str(user.id),
            "organization_id": str(org.id),
            "joined_date": "2026-02-01T00:00:00",
        },
    )
    assert response.status_code == 400
    assert "already a member" in response.json()["detail"]


def test_get_user_organizations(
    client, create_user, create_organization, create_user_organization, auth_headers
):
    user = create_user(username="member", email="member@example.com")
    org = create_organization(name="Test Company")
    create_user_organization(user_id=user.id, organization_id=org.id)

    response = client.get("/user-organizations", headers=auth_headers(user))
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_get_single_membership(
    client, create_user, create_organization, create_user_organization, auth_headers
):
    user = create_user(username="member", email="member@example.com")
    org = create_organization(name="Test Company")
    membership = create_user_organization(user_id=user.id, organization_id=org.id)

    response = client.get(
        f"/user-organizations/{membership.id}", headers=auth_headers(user)
    )
    assert response.status_code == 200
    assert response.json()["id"] == str(membership.id)


def test_get_organizations_for_user(
    client, create_user, create_organization, create_user_organization, auth_headers
):
    user = create_user(username="member", email="member@example.com")
    org1 = create_organization(name="Company A")
    org2 = create_organization(name="Company B")
    create_user_organization(user_id=user.id, organization_id=org1.id)
    create_user_organization(user_id=user.id, organization_id=org2.id)

    response = client.get(
        f"/users/{user.id}/organizations", headers=auth_headers(user)
    )
    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_get_members_for_organization(
    client, create_user, create_organization, create_user_organization, auth_headers
):
    user1 = create_user(username="member1", email="member1@example.com")
    user2 = create_user(username="member2", email="member2@example.com")
    org = create_organization(name="Test Company")
    create_user_organization(user_id=user1.id, organization_id=org.id)
    create_user_organization(user_id=user2.id, organization_id=org.id)

    response = client.get(
        f"/organizations/{org.id}/members", headers=auth_headers(user1)
    )
    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_update_membership_left_date(
    client, create_user, create_organization, create_user_organization, auth_headers
):
    user = create_user(username="member", email="member@example.com")
    org = create_organization(name="Test Company")
    membership = create_user_organization(user_id=user.id, organization_id=org.id)

    # User leaves the company
    response = client.patch(
        f"/user-organizations/{membership.id}",
        headers=auth_headers(user),
        json={
            "left_date": "2026-06-30T00:00:00",
            "is_active": False,
        },
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert response.json()["left_date"] is not None


def test_delete_membership(
    client, create_user, create_organization, create_user_organization, auth_headers
):
    user = create_user(username="member", email="member@example.com")
    org = create_organization(name="Test Company")
    membership = create_user_organization(user_id=user.id, organization_id=org.id)

    response = client.delete(
        f"/user-organizations/{membership.id}", headers=auth_headers(user)
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Membership deleted"


def test_membership_not_found(client, create_user, auth_headers):
    user = create_user(username="member", email="member@example.com")

    response = client.get(
        "/user-organizations/00000000-0000-0000-0000-000000000000",
        headers=auth_headers(user),
    )
    assert response.status_code == 404


def test_join_invalid_organization(client, create_user, auth_headers):
    user = create_user(username="member", email="member@example.com")

    response = client.post(
        "/user-organizations",
        headers=auth_headers(user),
        json={
            "user_id": str(user.id),
            "organization_id": "00000000-0000-0000-0000-000000000000",
            "joined_date": "2026-01-15T00:00:00",
        },
    )
    assert response.status_code == 404


def test_join_invalid_user(client, create_user, create_organization, auth_headers):
    user = create_user(username="member", email="member@example.com")
    org = create_organization(name="Test Company")

    response = client.post(
        "/user-organizations",
        headers=auth_headers(user),
        json={
            "user_id": "00000000-0000-0000-0000-000000000000",
            "organization_id": str(org.id),
            "joined_date": "2026-01-15T00:00:00",
        },
    )
    assert response.status_code == 404
