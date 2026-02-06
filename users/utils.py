from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from organizations.models import Organization
from users.choices import UserType
from users.models import LeaveRequestItem, User


def coerce_user_type(value: str) -> UserType:
    """Convert a string value to UserType enum."""
    normalized = value.strip().upper()
    try:
        return UserType[normalized]
    except KeyError:
        raise HTTPException(status_code=403, detail="Admin access required")


def require_admin(user_type: str) -> None:
    """Raise 403 if user is not an admin."""
    if coerce_user_type(user_type) != UserType.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")


def require_authenticated_user(request: Request):
    """Raise 401 if user is not authenticated."""
    if not request.user or not request.user.is_authenticated:
        raise HTTPException(status_code=401, detail="Authentication required")
    return request.user


def build_leave_request_item(row, db: Session) -> LeaveRequestItem:
    """Build LeaveRequestItem from a LeaveRequest row."""
    user = db.query(User).filter(User.id == row.user_id).first()
    org = db.query(Organization).filter(Organization.id == row.organization_id).first()
    reviewer = db.query(User).filter(User.id == row.reviewed_by).first() if row.reviewed_by else None
    return LeaveRequestItem(
        id=str(row.id),
        user_id=str(row.user_id),
        username=user.username if user else None,
        organization_id=str(row.organization_id),
        organization_name=org.name if org else None,
        date=row.date,
        leave_type=row.leave_type,
        reason=row.reason,
        is_accepted=row.is_accepted,
        reviewed_by=str(row.reviewed_by) if row.reviewed_by else None,
        reviewer_name=reviewer.username if reviewer else None,
        reviewed_at=row.reviewed_at,
        applied_at=row.applied_at,
        created=row.created,
    )
