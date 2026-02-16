from sqlalchemy import func

from database.db import SessionLocal
from organizations.models import Organization, Policy, UserOrganization
from users.models import LeaveRequest


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


def get_my_organization_details(user_id: str):
    """
    Get organization details for the given user by looking up their memberships
    in UserOrganization and returning the organizations they belong to.
    """
    with SessionLocal() as db:
        memberships = (
            db.query(UserOrganization)
            .filter(
                UserOrganization.user_id == user_id,
                UserOrganization.is_active.is_(True),
            )
            .order_by(UserOrganization.joined_date.desc())
            .all()
        )
        if not memberships:
            return {
                "detail": "You are not a member of any organization.",
                "organizations": [],
                "total": 0,
            }
        organizations = []
        for m in memberships:
            org = db.query(Organization).filter(Organization.id == m.organization_id).first()
            if org:
                organizations.append({
                    "id": str(org.id),
                    "name": org.name,
                    "description": org.description,
                    "address": org.address,
                    "email": org.email,
                    "phone": org.phone,
                    "is_active": org.is_active,
                    "membership_joined_date": str(m.joined_date) if m.joined_date else None,
                })
        return {
            "organizations": organizations,
            "total": len(organizations),
            "message": f"Found {len(organizations)} organization(s) you belong to.",
        }


def get_organization_ids_for_user(user_id: str) -> list[str]:
    """Return list of organization IDs (as strings) the user belongs to (active memberships)."""
    with SessionLocal() as db:
        rows = (
            db.query(UserOrganization.organization_id)
            .filter(
                UserOrganization.user_id == user_id,
                UserOrganization.is_active.is_(True),
            )
            .all()
        )
        return [str(r[0]) for r in rows]


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


def get_my_approved_leaves_summary(user_id: str) -> dict:
    """
    Get the count of approved leaves for the given user, grouped by organization and leave type.
    Used to compute pending/remaining leaves when combined with leave policy.
    """
    with SessionLocal() as db:
        rows = (
            db.query(
                LeaveRequest.organization_id,
                LeaveRequest.leave_type,
                func.count(LeaveRequest.id).label("count"),
            )
            .filter(
                LeaveRequest.user_id == user_id,
                LeaveRequest.is_accepted.is_(True),
            )
            .group_by(LeaveRequest.organization_id, LeaveRequest.leave_type)
            .all()
        )
        orgs = {}
        if rows:
            unique_org_ids = list({r[0] for r in rows})
            org_list = (
                db.query(Organization)
                .filter(Organization.id.in_(unique_org_ids))
                .all()
            )
            orgs = {str(o.id): o.name for o in org_list}

        by_org = {}
        total_approved = 0
        for org_id, leave_type, count in rows:
            org_name = orgs.get(str(org_id), "Unknown")
            if org_id not in by_org:
                by_org[str(org_id)] = {"organization_name": org_name, "by_type": {}, "total": 0}
            by_org[str(org_id)]["by_type"][str(leave_type.value)] = count
            by_org[str(org_id)]["total"] += count
            total_approved += count

        return {
            "approved_leaves": list(by_org.values()),
            "total_approved_days": total_approved,
            "organizations": list(by_org.keys()),
        }
