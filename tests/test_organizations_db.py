"""Unit tests for organizations.db helpers (get_my_organization_details, get_organization_ids_for_user)."""

import organizations.db as org_db


def test_get_my_organization_details_returns_orgs_for_user(
    app, create_user, create_organization, create_user_organization
):
    user = create_user(username="member", email="member@example.com")
    org = create_organization(name="Acme Corp", description="Test org")
    create_user_organization(user_id=user.id, organization_id=org.id)

    result = org_db.get_my_organization_details(str(user.id))

    assert result["total"] == 1
    assert len(result["organizations"]) == 1
    assert result["organizations"][0]["name"] == "Acme Corp"
    assert result["organizations"][0]["id"] == str(org.id)
    assert "membership_joined_date" in result["organizations"][0]
    assert "message" in result


def test_get_my_organization_details_returns_empty_when_user_has_no_orgs(app, create_user):
    user = create_user(username="loner", email="loner@example.com")

    result = org_db.get_my_organization_details(str(user.id))

    assert result["total"] == 0
    assert result["organizations"] == []
    assert "not a member" in result["detail"].lower()


def test_get_my_organization_details_ignores_inactive_membership(
    app, create_user, create_organization, create_user_organization
):
    user = create_user(username="inactive", email="inactive@example.com")
    org = create_organization(name="Left Org")
    create_user_organization(
        user_id=user.id,
        organization_id=org.id,
        is_active=False,
    )

    result = org_db.get_my_organization_details(str(user.id))

    assert result["total"] == 0
    assert result["organizations"] == []


def test_get_my_organization_details_multiple_orgs(
    app, create_user, create_organization, create_user_organization
):
    user = create_user(username="multi", email="multi@example.com")
    org1 = create_organization(name="Org One")
    org2 = create_organization(name="Org Two")
    create_user_organization(user_id=user.id, organization_id=org1.id)
    create_user_organization(user_id=user.id, organization_id=org2.id)

    result = org_db.get_my_organization_details(str(user.id))

    assert result["total"] == 2
    names = {o["name"] for o in result["organizations"]}
    assert names == {"Org One", "Org Two"}


def test_get_organization_ids_for_user_returns_ids(
    app, create_user, create_organization, create_user_organization
):
    user = create_user(username="u", email="u@example.com")
    org = create_organization(name="My Org")
    create_user_organization(user_id=user.id, organization_id=org.id)

    ids = org_db.get_organization_ids_for_user(str(user.id))

    assert len(ids) == 1
    assert ids[0] == str(org.id)


def test_get_organization_ids_for_user_empty_when_no_membership(app, create_user):
    user = create_user(username="nobody", email="nobody@example.com")

    ids = org_db.get_organization_ids_for_user(str(user.id))

    assert ids == []


def test_get_organization_ids_for_user_excludes_inactive(
    app, create_user, create_organization, create_user_organization
):
    user = create_user(username="ex", email="ex@example.com")
    org = create_organization(name="Ex Org")
    create_user_organization(
        user_id=user.id,
        organization_id=org.id,
        is_active=False,
    )

    ids = org_db.get_organization_ids_for_user(str(user.id))

    assert ids == []


def test_get_my_approved_leaves_summary_empty_when_no_approved_leaves(
    app, create_user, create_organization, create_user_organization
):
    user = create_user(username="no-leaves", email="no-leaves@example.com")
    org = create_organization(name="Leave Org")
    create_user_organization(user_id=user.id, organization_id=org.id)

    result = org_db.get_my_approved_leaves_summary(str(user.id))

    assert result["total_approved_days"] == 0
    assert result["approved_leaves"] == []
    assert result["organizations"] == []


def test_get_my_approved_leaves_summary_counts_approved_only(
    app,
    create_user,
    create_organization,
    create_user_organization,
    create_leave_request,
):
    from users.choices import LeaveType

    user = create_user(username="leave-user", email="leave@example.com")
    org = create_organization(name="Leave Org")
    create_user_organization(user_id=user.id, organization_id=org.id)

    create_leave_request(
        user_id=user.id, organization_id=org.id, is_accepted=True, leave_type=LeaveType.SICK_LEAVE
    )
    create_leave_request(
        user_id=user.id, organization_id=org.id, is_accepted=True, leave_type=LeaveType.SICK_LEAVE
    )
    create_leave_request(
        user_id=user.id,
        organization_id=org.id,
        is_accepted=False,
        leave_type=LeaveType.PRIVILEGE_LEAVE,
    )

    result = org_db.get_my_approved_leaves_summary(str(user.id))

    assert result["total_approved_days"] == 2
    assert len(result["approved_leaves"]) == 1
    assert result["approved_leaves"][0]["organization_name"] == "Leave Org"
    assert result["approved_leaves"][0]["by_type"]["SICK_LEAVE"] == 2
    assert result["approved_leaves"][0]["total"] == 2


def test_get_my_approved_leaves_summary_grouped_by_org_and_type(
    app,
    create_user,
    create_organization,
    create_user_organization,
    create_leave_request,
):
    from users.choices import LeaveType

    user = create_user(username="multi-leave", email="multi@example.com")
    org1 = create_organization(name="Org A")
    org2 = create_organization(name="Org B")
    create_user_organization(user_id=user.id, organization_id=org1.id)
    create_user_organization(user_id=user.id, organization_id=org2.id)

    create_leave_request(
        user_id=user.id, organization_id=org1.id, is_accepted=True, leave_type=LeaveType.SICK_LEAVE
    )
    create_leave_request(
        user_id=user.id,
        organization_id=org1.id,
        is_accepted=True,
        leave_type=LeaveType.PRIVILEGE_LEAVE,
    )
    create_leave_request(
        user_id=user.id, organization_id=org2.id, is_accepted=True, leave_type=LeaveType.SICK_LEAVE
    )

    result = org_db.get_my_approved_leaves_summary(str(user.id))

    assert result["total_approved_days"] == 3
    assert len(result["approved_leaves"]) == 2
    org_names = {a["organization_name"] for a in result["approved_leaves"]}
    assert org_names == {"Org A", "Org B"}
