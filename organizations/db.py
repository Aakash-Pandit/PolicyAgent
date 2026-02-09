from sqlalchemy import func

from database.db import SessionLocal
from organizations.models import Organization, Policy


def get_organization_details(organization_name: str):
    """Get organization details by name."""
    with SessionLocal() as db:
        org = (
            db.query(Organization)
            .filter(func.lower(Organization.name).contains(organization_name.lower()))
            .first()
        )
        if org:
            return {
                "id": str(org.id),
                "name": org.name,
                "description": org.description,
                "address": org.address,
                "email": org.email,
                "phone": org.phone,
                "is_active": org.is_active,
            }
        return {"detail": "Organization not found", "name": organization_name}


def get_policies_for_organization(organization_name: str):
    """Get all policies for an organization."""
    with SessionLocal() as db:
        org = (
            db.query(Organization)
            .filter(func.lower(Organization.name).contains(organization_name.lower()))
            .first()
        )
        if not org:
            return {"detail": "Organization not found", "policies": []}

        policies = (
            db.query(Policy)
            .filter(Policy.organization_id == org.id, Policy.is_active.is_(True))
            .all()
        )
        return {
            "organization": org.name,
            "policies": [
                {
                    "id": str(policy.id),
                    "name": policy.name,
                    "description": policy.description,
                    "document_name": policy.document_name,
                    "file_path": policy.file,
                    "is_active": policy.is_active,
                }
                for policy in policies
            ],
            "total": len(policies),
        }


def get_policy_details(policy_name: str, organization_name: str):
    """Get policy details by name."""
    with SessionLocal() as db:
        policy = (
            db.query(Policy)
            .filter(func.lower(Policy.name).contains(policy_name.lower()))
            .filter(func.lower(Organization.name).contains(organization_name.lower()))
            .first()
        )
        if policy:
            return {
                "id": str(policy.id),
                "name": policy.name,
                "description": policy.description,
                "document_name": policy.document_name,
                "file_path": policy.file,
                "is_active": policy.is_active,
                "organization": organization_name,
            }
        return {"detail": "Policy not found", "name": policy_name}
