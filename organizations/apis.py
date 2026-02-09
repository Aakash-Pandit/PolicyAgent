import logging

from fastapi import Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from application.app import app
from ai.rag import RAGClient
from database.db import get_db
from organizations.models import (
    Organization,
    OrganizationItem,
    OrganizationRequest,
    OrganizationResponse,
    OrganizationsListResponse,
    Policy,
    PolicyItem,
    PolicyResponse,
    PoliciesListResponse,
    UserOrganization,
    UserOrganizationItem,
    UserOrganizationRequest,
    UserOrganizationResponse,
    UserOrganizationsListResponse,
    UserOrganizationUpdate,
)
from organizations.utils import delete_file_if_exists, save_upload_file
from users.models import User

logger = logging.getLogger(__name__)


# Organization APIs
@app.get("/organizations", response_model=OrganizationsListResponse)
async def get_organizations(db: Session = Depends(get_db)):
    rows = db.query(Organization).order_by(Organization.created.desc()).all()
    organizations = [
        OrganizationItem(
            id=str(row.id),
            name=row.name,
            description=row.description,
            address=row.address,
            email=row.email,
            phone=row.phone,
            is_active=row.is_active,
            created=row.created,
        )
        for row in rows
    ]
    total = len(organizations)
    message = "No organizations found" if total == 0 else "Organizations retrieved"
    return OrganizationsListResponse(
        organizations=organizations,
        total=total,
        message=message,
    )


@app.get("/organizations/{organization_id}", response_model=OrganizationItem)
async def get_organization(organization_id: str, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return OrganizationItem(
        id=str(org.id),
        name=org.name,
        description=org.description,
        address=org.address,
        email=org.email,
        phone=org.phone,
        is_active=org.is_active,
        created=org.created,
    )


@app.post("/organizations", response_model=OrganizationResponse)
async def create_organization(
    organization: OrganizationRequest, db: Session = Depends(get_db)
):
    # Check if organization with same name exists
    existing = db.query(Organization).filter(Organization.name == organization.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Organization with this name already exists")

    new_org = Organization(
        name=organization.name,
        description=organization.description,
        address=organization.address,
        email=organization.email,
        phone=organization.phone,
        is_active=organization.is_active,
    )
    db.add(new_org)
    db.commit()
    db.refresh(new_org)

    return OrganizationResponse(
        id=str(new_org.id),
        name=new_org.name,
        description=new_org.description,
        address=new_org.address,
        email=new_org.email,
        phone=new_org.phone,
        is_active=new_org.is_active,
    )


@app.put("/organizations/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: str,
    organization: OrganizationRequest,
    db: Session = Depends(get_db),
):
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    org.name = organization.name
    org.description = organization.description
    org.address = organization.address
    org.email = organization.email
    org.phone = organization.phone
    org.is_active = organization.is_active
    db.commit()
    db.refresh(org)

    return OrganizationResponse(
        id=str(org.id),
        name=org.name,
        description=org.description,
        address=org.address,
        email=org.email,
        phone=org.phone,
        is_active=org.is_active,
    )


@app.delete("/organizations/{organization_id}")
async def delete_organization(organization_id: str, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    db.delete(org)
    db.commit()
    return {"status": "ok", "message": "Organization deleted"}


# Policy APIs
@app.get("/policies", response_model=PoliciesListResponse)
async def get_policies(db: Session = Depends(get_db)):
    rows = db.query(Policy).order_by(Policy.created.desc()).all()
    policies = []
    for row in rows:
        org = db.query(Organization).filter(Organization.id == row.organization_id).first()
        policies.append(
            PolicyItem(
                id=str(row.id),
                organization_id=str(row.organization_id),
                organization_name=org.name if org else None,
                name=row.name,
                description=row.description,
                document_name=row.document_name,
                file_path=row.file,
                is_active=row.is_active,
                created=row.created,
            )
        )
    total = len(policies)
    message = "No policies found" if total == 0 else "Policies retrieved"
    return PoliciesListResponse(
        policies=policies,
        total=total,
        message=message,
    )


@app.get("/policies/{policy_id}", response_model=PolicyItem)
async def get_policy(policy_id: str, db: Session = Depends(get_db)):
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    org = db.query(Organization).filter(Organization.id == policy.organization_id).first()
    return PolicyItem(
        id=str(policy.id),
        organization_id=str(policy.organization_id),
        organization_name=org.name if org else None,
        name=policy.name,
        description=policy.description,
        document_name=policy.document_name,
        file_path=policy.file,
        is_active=policy.is_active,
        created=policy.created,
    )


@app.get("/organizations/{organization_id}/policies", response_model=PoliciesListResponse)
async def get_organization_policies(organization_id: str, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    rows = db.query(Policy).filter(Policy.organization_id == organization_id).order_by(Policy.created.desc()).all()
    policies = [
        PolicyItem(
            id=str(row.id),
            organization_id=str(row.organization_id),
            organization_name=org.name,
            name=row.name,
            description=row.description,
            document_name=row.document_name,
            file_path=row.file,
            is_active=row.is_active,
            created=row.created,
        )
        for row in rows
    ]
    total = len(policies)
    message = "No policies found" if total == 0 else "Policies retrieved"
    return PoliciesListResponse(
        policies=policies,
        total=total,
        message=message,
    )


@app.post("/policies", response_model=PolicyResponse)
async def create_policy(
    organization_id: str = Form(...),
    name: str = Form(...),
    description: str = Form(None),
    is_active: bool = Form(True),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    # Verify organization exists
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Handle file upload
    file_path = None
    document_name = None
    if file and file.filename:
        document_name = file.filename
        file_path = await save_upload_file(file)

    new_policy = Policy(
        organization_id=organization_id,
        name=name,
        description=description,
        document_name=document_name,
        file=file_path,
        is_active=is_active,
    )
    db.add(new_policy)
    db.commit()
    db.refresh(new_policy)
    if file_path:
        try:
            RAGClient().index_policy_document(
                policy_id=str(new_policy.id),
                organization_id=str(new_policy.organization_id),
                policy_name=new_policy.name,
                description=new_policy.description,
                document_name=new_policy.document_name,
                file_path=file_path,
            )
        except Exception as exc:
            logger.exception("Failed to index policy document", extra={"error": str(exc)})

    return PolicyResponse(
        id=str(new_policy.id),
        organization_id=str(new_policy.organization_id),
        name=new_policy.name,
        description=new_policy.description,
        document_name=new_policy.document_name,
        file_path=new_policy.file,
        is_active=new_policy.is_active,
    )


@app.put("/policies/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: str,
    organization_id: str = Form(...),
    name: str = Form(...),
    description: str = Form(None),
    is_active: bool = Form(True),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    existing_policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not existing_policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    # Verify organization exists
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Handle file upload
    if file and file.filename:
        # Delete old file if exists
        delete_file_if_exists(existing_policy.file)
        existing_policy.document_name = file.filename
        existing_policy.file = await save_upload_file(file)

    existing_policy.organization_id = organization_id
    existing_policy.name = name
    existing_policy.description = description
    existing_policy.is_active = is_active
    db.commit()
    db.refresh(existing_policy)
    if file and file.filename and existing_policy.file:
        try:
            RAGClient().index_policy_document(
                policy_id=str(existing_policy.id),
                organization_id=str(existing_policy.organization_id),
                policy_name=existing_policy.name,
                description=existing_policy.description,
                document_name=existing_policy.document_name,
                file_path=existing_policy.file,
            )
        except Exception as exc:
            logger.exception("Failed to reindex policy document", extra={"error": str(exc)})

    return PolicyResponse(
        id=str(existing_policy.id),
        organization_id=str(existing_policy.organization_id),
        name=existing_policy.name,
        description=existing_policy.description,
        document_name=existing_policy.document_name,
        file_path=existing_policy.file,
        is_active=existing_policy.is_active,
    )


@app.delete("/policies/{policy_id}")
async def delete_policy(policy_id: str, db: Session = Depends(get_db)):
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    # Delete associated file if exists
    delete_file_if_exists(policy.file)
    try:
        RAGClient().remove_policy_from_index(str(policy.id))
    except Exception as exc:
        logger.exception("Failed to remove policy from index", extra={"error": str(exc)})

    db.delete(policy)
    db.commit()
    return {"status": "ok", "message": "Policy deleted"}


# User Organization (Membership) APIs
@app.get("/user_organizations", response_model=UserOrganizationsListResponse)
async def get_user_organizations(db: Session = Depends(get_db)):
    """Get all user-organization memberships."""
    rows = db.query(UserOrganization).order_by(UserOrganization.created.desc()).all()
    memberships = []
    for row in rows:
        user = db.query(User).filter(User.id == row.user_id).first()
        org = db.query(Organization).filter(Organization.id == row.organization_id).first()
        memberships.append(
            UserOrganizationItem(
                id=str(row.id),
                user_id=str(row.user_id),
                username=user.username if user else None,
                organization_id=str(row.organization_id),
                organization_name=org.name if org else None,
                joined_date=row.joined_date,
                left_date=row.left_date,
                is_active=row.is_active,
                created=row.created,
            )
        )
    total = len(memberships)
    message = "No memberships found" if total == 0 else "Memberships retrieved"
    return UserOrganizationsListResponse(
        memberships=memberships,
        total=total,
        message=message,
    )


@app.get("/user_organizations/{membership_id}", response_model=UserOrganizationItem)
async def get_user_organization(membership_id: str, db: Session = Depends(get_db)):
    """Get a specific user-organization membership."""
    membership = db.query(UserOrganization).filter(UserOrganization.id == membership_id).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")

    user = db.query(User).filter(User.id == membership.user_id).first()
    org = db.query(Organization).filter(Organization.id == membership.organization_id).first()
    return UserOrganizationItem(
        id=str(membership.id),
        user_id=str(membership.user_id),
        username=user.username if user else None,
        organization_id=str(membership.organization_id),
        organization_name=org.name if org else None,
        joined_date=membership.joined_date,
        left_date=membership.left_date,
        is_active=membership.is_active,
        created=membership.created,
    )


@app.get("/organizations/{organization_id}/members", response_model=UserOrganizationsListResponse)
async def get_members_for_organization(organization_id: str, db: Session = Depends(get_db)):
    """Get all members of an organization."""
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    rows = db.query(UserOrganization).filter(UserOrganization.organization_id == organization_id).order_by(UserOrganization.joined_date.desc()).all()
    memberships = []
    for row in rows:
        user = db.query(User).filter(User.id == row.user_id).first()
        memberships.append(
            UserOrganizationItem(
                id=str(row.id),
                user_id=str(row.user_id),
                username=user.username if user else None,
                organization_id=str(row.organization_id),
                organization_name=org.name,
                joined_date=row.joined_date,
                left_date=row.left_date,
                is_active=row.is_active,
                created=row.created,
            )
        )
    total = len(memberships)
    message = "No members found" if total == 0 else "Members retrieved"
    return UserOrganizationsListResponse(
        memberships=memberships,
        total=total,
        message=message,
    )


@app.post("/user_organizations", response_model=UserOrganizationResponse)
async def join_organization(
    membership: UserOrganizationRequest,
    db: Session = Depends(get_db),
):
    """Add a user to an organization (join)."""
    # Verify user exists
    user = db.query(User).filter(User.id == membership.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify organization exists
    org = db.query(Organization).filter(Organization.id == membership.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Check if already a member
    existing = (
        db.query(UserOrganization)
        .filter(
            UserOrganization.user_id == membership.user_id,
            UserOrganization.organization_id == membership.organization_id,
            UserOrganization.is_active.is_(True),
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member of this organization")

    new_membership = UserOrganization(
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        joined_date=membership.joined_date.date(),
        left_date=membership.left_date.date() if membership.left_date else None,
        is_active=membership.is_active,
    )
    db.add(new_membership)
    db.commit()
    db.refresh(new_membership)

    return UserOrganizationResponse(
        id=str(new_membership.id),
        user_id=str(new_membership.user_id),
        organization_id=str(new_membership.organization_id),
        joined_date=new_membership.joined_date,
        left_date=new_membership.left_date,
        is_active=new_membership.is_active,
    )


@app.patch("/user_organizations/{membership_id}", response_model=UserOrganizationResponse)
async def update_membership(
    membership_id: str,
    update: UserOrganizationUpdate,
    db: Session = Depends(get_db),
):
    """Update a user-organization membership (e.g., set left_date when leaving)."""
    membership = db.query(UserOrganization).filter(UserOrganization.id == membership_id).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")

    if update.joined_date is not None:
        membership.joined_date = update.joined_date.date()
    if update.left_date is not None:
        membership.left_date = update.left_date.date()
    if update.is_active is not None:
        membership.is_active = update.is_active

    db.commit()
    db.refresh(membership)

    return UserOrganizationResponse(
        id=str(membership.id),
        user_id=str(membership.user_id),
        organization_id=str(membership.organization_id),
        joined_date=membership.joined_date,
        left_date=membership.left_date,
        is_active=membership.is_active,
    )


@app.delete("/user_organizations/{membership_id}")
async def delete_membership(membership_id: str, db: Session = Depends(get_db)):
    """Delete a user-organization membership record."""
    membership = db.query(UserOrganization).filter(UserOrganization.id == membership_id).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")
    db.delete(membership)
    db.commit()
    return {"status": "ok", "message": "Membership deleted"}
