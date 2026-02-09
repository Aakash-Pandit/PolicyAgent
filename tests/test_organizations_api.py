def test_organizations_crud(client, create_user, auth_headers):
    user = create_user(username="org-user", email="org-user@example.com")

    # Create organization
    create_response = client.post(
        "/organizations",
        headers=auth_headers(user),
        json={
            "name": "Acme Corp",
            "description": "A test organization",
            "address": "123 Main St",
            "email": "info@acme.com",
            "phone": "555-0100",
            "is_active": True,
        },
    )
    assert create_response.status_code == 200
    org_id = create_response.json()["id"]
    assert create_response.json()["name"] == "Acme Corp"

    # List organizations
    list_response = client.get("/organizations", headers=auth_headers(user))
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    # Get organization
    get_response = client.get(f"/organizations/{org_id}", headers=auth_headers(user))
    assert get_response.status_code == 200
    assert get_response.json()["id"] == org_id

    # Update organization
    update_response = client.put(
        f"/organizations/{org_id}",
        headers=auth_headers(user),
        json={
            "name": "Acme Corporation",
            "description": "Updated description",
            "address": "456 Oak Ave",
            "email": "contact@acme.com",
            "phone": "555-0200",
            "is_active": True,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Acme Corporation"

    # Delete organization
    delete_response = client.delete(f"/organizations/{org_id}", headers=auth_headers(user))
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Organization deleted"


def test_organization_not_found(client, create_user, auth_headers):
    user = create_user(username="org-user", email="org-user@example.com")
    response = client.get(
        "/organizations/00000000-0000-0000-0000-000000000000",
        headers=auth_headers(user),
    )
    assert response.status_code == 404


def test_policies_crud(client, create_user, create_organization, auth_headers):
    user = create_user(username="policy-user", email="policy-user@example.com")
    org = create_organization(name="Test Org")

    # Create policy (using form data for file upload support)
    create_response = client.post(
        "/policies",
        headers=auth_headers(user),
        data={
            "organization_id": str(org.id),
            "name": "Standard Leave Policy",
            "description": "Standard policy for all employees",
            "is_active": "true",
        },
    )
    assert create_response.status_code == 200
    policy_id = create_response.json()["id"]
    assert create_response.json()["name"] == "Standard Leave Policy"

    # List policies
    list_response = client.get("/policies", headers=auth_headers(user))
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    # Get policy
    get_response = client.get(f"/policies/{policy_id}", headers=auth_headers(user))
    assert get_response.status_code == 200
    assert get_response.json()["id"] == policy_id

    # Get organization policies
    org_policies_response = client.get(
        f"/organizations/{org.id}/policies", headers=auth_headers(user)
    )
    assert org_policies_response.status_code == 200
    assert org_policies_response.json()["total"] == 1

    # Update policy (using form data)
    update_response = client.put(
        f"/policies/{policy_id}",
        headers=auth_headers(user),
        data={
            "organization_id": str(org.id),
            "name": "Updated Leave Policy",
            "description": "Updated description",
            "is_active": "true",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Updated Leave Policy"

    # Delete policy
    delete_response = client.delete(f"/policies/{policy_id}", headers=auth_headers(user))
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Policy deleted"


def test_policy_not_found(client, create_user, auth_headers):
    user = create_user(username="policy-user", email="policy-user@example.com")
    response = client.get(
        "/policies/00000000-0000-0000-0000-000000000000",
        headers=auth_headers(user),
    )
    assert response.status_code == 404


def test_policy_requires_valid_organization(client, create_user, auth_headers):
    user = create_user(username="policy-user", email="policy-user@example.com")
    response = client.post(
        "/policies",
        headers=auth_headers(user),
        data={
            "organization_id": "00000000-0000-0000-0000-000000000000",
            "name": "Invalid Policy",
        },
    )
    assert response.status_code == 404


def test_policy_with_file_upload(client, create_user, create_organization, auth_headers):
    import io

    user = create_user(username="file-user", email="file-user@example.com")
    org = create_organization(name="File Test Org")

    # Create a test file
    test_file_content = b"This is a test policy document content."
    test_file = io.BytesIO(test_file_content)

    # Create policy with file upload
    create_response = client.post(
        "/policies",
        headers=auth_headers(user),
        data={
            "organization_id": str(org.id),
            "name": "Policy With File",
            "description": "Policy with uploaded document",
            "is_active": "true",
        },
        files={"file": ("test_policy.pdf", test_file, "application/pdf")},
    )
    assert create_response.status_code == 200
    assert create_response.json()["document_name"] == "test_policy.pdf"
    assert create_response.json()["file_path"] is not None

    # Clean up - delete the policy
    policy_id = create_response.json()["id"]
    client.delete(f"/policies/{policy_id}", headers=auth_headers(user))
