from datetime import datetime

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from application.app import app
from database.db import get_db
from organizations.models import (
    Organization,
    OrganizationItem,
    OrganizationRequest,
    OrganizationResponse,
    OrganizationsListResponse,
    Policy,
    PolicyItem,
    PolicyRequest,
    PolicyResponse,
    PoliciesListResponse,
)


# Organization APIs
@app.get("/organizations", response_model=OrganizationsListResponse)
async def get_organizations(db: Session = Depends(get_db)):
    rows = db.query(Organization).order_by(Organization.created_at.desc()).all()
    organizations = [
        OrganizationItem(
            id=str(row.id),
            name=row.name,
            description=row.description,
            address=row.address,
            email=row.email,
            phone=row.phone,
            is_active=row.is_active,
            created_at=row.created_at,
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
        created_at=org.created_at,
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
    rows = db.query(Policy).order_by(Policy.created_at.desc()).all()
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
                max_leave_days=row.max_leave_days,
                carry_forward_days=row.carry_forward_days,
                is_active=row.is_active,
                created_at=row.created_at,
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
        max_leave_days=policy.max_leave_days,
        carry_forward_days=policy.carry_forward_days,
        is_active=policy.is_active,
        created_at=policy.created_at,
    )


@app.get("/organizations/{organization_id}/policies", response_model=PoliciesListResponse)
async def get_organization_policies(organization_id: str, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    rows = db.query(Policy).filter(Policy.organization_id == organization_id).order_by(Policy.created_at.desc()).all()
    policies = [
        PolicyItem(
            id=str(row.id),
            organization_id=str(row.organization_id),
            organization_name=org.name,
            name=row.name,
            description=row.description,
            max_leave_days=row.max_leave_days,
            carry_forward_days=row.carry_forward_days,
            is_active=row.is_active,
            created_at=row.created_at,
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
async def create_policy(policy: PolicyRequest, db: Session = Depends(get_db)):
    # Verify organization exists
    org = db.query(Organization).filter(Organization.id == policy.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    new_policy = Policy(
        organization_id=policy.organization_id,
        name=policy.name,
        description=policy.description,
        max_leave_days=policy.max_leave_days,
        carry_forward_days=policy.carry_forward_days,
        is_active=policy.is_active,
    )
    db.add(new_policy)
    db.commit()
    db.refresh(new_policy)

    return PolicyResponse(
        id=str(new_policy.id),
        organization_id=str(new_policy.organization_id),
        name=new_policy.name,
        description=new_policy.description,
        max_leave_days=new_policy.max_leave_days,
        carry_forward_days=new_policy.carry_forward_days,
        is_active=new_policy.is_active,
    )


@app.put("/policies/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: str,
    policy: PolicyRequest,
    db: Session = Depends(get_db),
):
    existing_policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not existing_policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    # Verify organization exists
    org = db.query(Organization).filter(Organization.id == policy.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    existing_policy.organization_id = policy.organization_id
    existing_policy.name = policy.name
    existing_policy.description = policy.description
    existing_policy.max_leave_days = policy.max_leave_days
    existing_policy.carry_forward_days = policy.carry_forward_days
    existing_policy.is_active = policy.is_active
    db.commit()
    db.refresh(existing_policy)

    return PolicyResponse(
        id=str(existing_policy.id),
        organization_id=str(existing_policy.organization_id),
        name=existing_policy.name,
        description=existing_policy.description,
        max_leave_days=existing_policy.max_leave_days,
        carry_forward_days=existing_policy.carry_forward_days,
        is_active=existing_policy.is_active,
    )


@app.delete("/policies/{policy_id}")
async def delete_policy(policy_id: str, db: Session = Depends(get_db)):
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    db.delete(policy)
    db.commit()
    return {"status": "ok", "message": "Policy deleted"}
