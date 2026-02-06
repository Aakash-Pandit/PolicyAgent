from sqlalchemy import func

from database.db import SessionLocal
from organizations.models import Organization, Policy


def get_organization_by_name(name: str):
    """Get organization details by name."""
    with SessionLocal() as db:
        org = (
            db.query(Organization)
            .filter(func.lower(Organization.name).contains(name.lower()))
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
        return {"detail": "Organization not found", "name": name}


def get_all_organizations():
    """Get all active organizations."""
    with SessionLocal() as db:
        orgs = (
            db.query(Organization)
            .filter(Organization.is_active == True)
            .order_by(Organization.name)
            .all()
        )
        return {
            "organizations": [
                {
                    "id": str(org.id),
                    "name": org.name,
                    "description": org.description,
                    "is_active": org.is_active,
                }
                for org in orgs
            ],
            "total": len(orgs),
        }


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
            .filter(Policy.organization_id == org.id, Policy.is_active == True)
            .all()
        )
        return {
            "organization": org.name,
            "policies": [
                {
                    "id": str(policy.id),
                    "name": policy.name,
                    "description": policy.description,
                    "max_leave_days": policy.max_leave_days,
                    "carry_forward_days": policy.carry_forward_days,
                    "is_active": policy.is_active,
                }
                for policy in policies
            ],
            "total": len(policies),
        }


def get_policy_details(policy_name: str):
    """Get policy details by name."""
    with SessionLocal() as db:
        policy = (
            db.query(Policy)
            .filter(func.lower(Policy.name).contains(policy_name.lower()))
            .first()
        )
        if policy:
            org = db.query(Organization).filter(Organization.id == policy.organization_id).first()
            return {
                "id": str(policy.id),
                "name": policy.name,
                "description": policy.description,
                "max_leave_days": policy.max_leave_days,
                "carry_forward_days": policy.carry_forward_days,
                "is_active": policy.is_active,
                "organization": org.name if org else None,
            }
        return {"detail": "Policy not found", "name": policy_name}


def get_leave_allowance(organization_name: str, policy_name: str | None = None):
    """Get leave allowance for an organization or specific policy."""
    with SessionLocal() as db:
        org = (
            db.query(Organization)
            .filter(func.lower(Organization.name).contains(organization_name.lower()))
            .first()
        )
        if not org:
            return {"detail": "Organization not found"}

        query = db.query(Policy).filter(
            Policy.organization_id == org.id,
            Policy.is_active == True,
        )
        
        if policy_name:
            query = query.filter(func.lower(Policy.name).contains(policy_name.lower()))
        
        policies = query.all()
        
        if not policies:
            return {"detail": "No policies found", "organization": org.name}

        return {
            "organization": org.name,
            "leave_policies": [
                {
                    "policy_name": p.name,
                    "max_leave_days": p.max_leave_days,
                    "carry_forward_days": p.carry_forward_days,
                }
                for p in policies
            ],
        }
