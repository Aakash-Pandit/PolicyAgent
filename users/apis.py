from datetime import datetime

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from application.app import app
from auth.passwords import hash_password
from database.db import drop_leave_requests_table, drop_users_table, get_db
from organizations.models import (
    Organization,
    UserOrganization,
    UserOrganizationItem,
    UserOrganizationsListResponse,
)
from users.choices import UserType
from users.models import (
    LeaveRequest,
    LeaveRequestCreate,
    LeaveRequestItem,
    LeaveRequestResponse,
    LeaveRequestReview,
    LeaveRequestsListResponse,
    User,
    UserItem,
    UserRequest,
    UserResponse,
    UsersListResponse,
)
from users.utils import (
    build_leave_request_item,
    coerce_user_type,
    require_admin,
    require_authenticated_user,
)


@app.get("/users", response_model=UsersListResponse)
async def get_users(
    request: Request,
    db: Session = Depends(get_db),
):
    require_admin(request.user.user_type)
    rows = db.query(User).order_by(User.created.desc()).all()
    users = [
        UserItem(
            id=str(row.id),
            first_name=row.first_name,
            last_name=row.last_name,
            username=row.username,
            email=row.email,
            phone=row.phone,
            gender=row.gender,
            user_type=row.user_type,
            date_of_birth=row.date_of_birth,
        )
        for row in rows
    ]
    total = len(users)
    message = "No users found" if total == 0 else "Users retrieved"
    return UsersListResponse(
        users=users,
        total=total,
        message=message,
    )


@app.get("/users/{user_id}", response_model=UserItem)
async def get_user(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    current_user = require_authenticated_user(request)
    if current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="User access restricted")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserItem(
        id=str(user.id),
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        email=user.email,
        phone=user.phone,
        gender=user.gender,
        user_type=user.user_type,
        date_of_birth=user.date_of_birth,
    )


@app.get("/users/{user_id}/organizations", response_model=UserOrganizationsListResponse)
async def get_organizations_for_user(user_id: str, db: Session = Depends(get_db)):
    """Get all organizations a user belongs to."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    rows = (
        db.query(UserOrganization)
        .filter(UserOrganization.user_id == user_id)
        .order_by(UserOrganization.joined_date.desc())
        .all()
    )
    memberships = []
    for row in rows:
        org = db.query(Organization).filter(Organization.id == row.organization_id).first()
        memberships.append(
            UserOrganizationItem(
                id=str(row.id),
                user_id=str(row.user_id),
                username=user.username,
                organization_id=str(row.organization_id),
                organization_name=org.name if org else None,
                joined_date=row.joined_date,
                left_date=row.left_date,
                is_active=row.is_active,
                created=row.created,
            )
        )
    total = len(memberships)
    message = "No organizations found for user" if total == 0 else "Organizations retrieved"
    return UserOrganizationsListResponse(
        memberships=memberships,
        total=total,
        message=message,
    )


@app.post("/users", response_model=UserResponse)
async def create_user(user: UserRequest, db: Session = Depends(get_db)):
    password_hash = hash_password(user.password)
    new_user = User(
        first_name=user.first_name.lower(),
        last_name=user.last_name.lower(),
        username=user.username.lower(),
        password_hash=password_hash,
        email=user.email,
        phone=user.phone,
        gender=user.gender,
        date_of_birth=user.date_of_birth,
        user_type=user.user_type,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(
        id=str(new_user.id),
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        username=new_user.username,
        email=new_user.email,
        phone=new_user.phone,
        gender=new_user.gender,
        user_type=new_user.user_type,
        date_of_birth=new_user.date_of_birth,
    )


@app.delete("/users/{user_id}")
async def delete_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"status": "ok", "message": "User deleted"}


@app.delete("/admin/drop-users-db")
async def drop_users_db_table():
    drop_users_table()
    return {"status": "ok", "message": "Users database table dropped"}


# Leave Request APIs
@app.get("/leave-requests", response_model=LeaveRequestsListResponse)
async def get_leave_requests(
    request: Request,
    db: Session = Depends(get_db),
):
    """Get all leave requests. Admin sees all, regular users see only their own."""
    current_user = require_authenticated_user(request)

    if coerce_user_type(current_user.user_type) == UserType.ADMIN:
        rows = db.query(LeaveRequest).order_by(LeaveRequest.applied_at.desc()).all()
    else:
        rows = (
            db.query(LeaveRequest)
            .filter(LeaveRequest.user_id == current_user.user_id)
            .order_by(LeaveRequest.applied_at.desc())
            .all()
        )

    leave_requests = [build_leave_request_item(row, db) for row in rows]

    total = len(leave_requests)
    message = "No leave requests found" if total == 0 else "Leave requests retrieved"
    return LeaveRequestsListResponse(
        leave_requests=leave_requests,
        total=total,
        message=message,
    )


@app.get("/leave-requests/{leave_request_id}", response_model=LeaveRequestItem)
async def get_leave_request(
    leave_request_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Get a specific leave request."""
    current_user = require_authenticated_user(request)

    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == leave_request_id).first()
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")

    # Regular users can only see their own leave requests
    if (
        coerce_user_type(current_user.user_type) != UserType.ADMIN
        and str(leave_request.user_id) != current_user.user_id
    ):
        raise HTTPException(status_code=403, detail="Access denied")

    return build_leave_request_item(leave_request, db)


@app.get("/organizations/{organization_id}/leave-requests", response_model=LeaveRequestsListResponse)
async def get_organization_leave_requests(
    organization_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Get all leave requests for an organization. Admin only."""
    require_admin(request.user.user_type)

    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    rows = (
        db.query(LeaveRequest)
        .filter(LeaveRequest.organization_id == organization_id)
        .order_by(LeaveRequest.applied_at.desc())
        .all()
    )

    leave_requests = [build_leave_request_item(row, db) for row in rows]

    total = len(leave_requests)
    message = "No leave requests found" if total == 0 else "Leave requests retrieved"
    return LeaveRequestsListResponse(
        leave_requests=leave_requests,
        total=total,
        message=message,
    )


@app.post("/leave-requests", response_model=LeaveRequestResponse)
async def apply_leave_request(
    leave_request: LeaveRequestCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Apply for a leave request. User must be a member of the organization."""
    current_user = require_authenticated_user(request)

    # Verify organization exists
    org = db.query(Organization).filter(Organization.id == leave_request.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Verify user is an active member of the organization
    membership = (
        db.query(UserOrganization)
        .filter(
            UserOrganization.user_id == current_user.user_id,
            UserOrganization.organization_id == leave_request.organization_id,
            UserOrganization.is_active.is_(True),
        )
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=403, detail="You are not an active member of this organization"
        )

    # Check if user already has a leave request for the same date in this organization
    existing = (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.user_id == current_user.user_id,
            LeaveRequest.organization_id == leave_request.organization_id,
            LeaveRequest.date == leave_request.date.date(),
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400, detail="You already have a leave request for this date in this organization"
        )

    new_leave_request = LeaveRequest(
        user_id=current_user.user_id,
        organization_id=leave_request.organization_id,
        date=leave_request.date.date(),
        leave_type=leave_request.leave_type,
        reason=leave_request.reason,
        is_accepted=False,
    )
    db.add(new_leave_request)
    db.commit()
    db.refresh(new_leave_request)

    return LeaveRequestResponse(
        id=str(new_leave_request.id),
        user_id=str(new_leave_request.user_id),
        organization_id=str(new_leave_request.organization_id),
        date=new_leave_request.date,
        leave_type=new_leave_request.leave_type,
        reason=new_leave_request.reason,
        is_accepted=new_leave_request.is_accepted,
        reviewed_by=None,
        reviewed_at=None,
        applied_at=new_leave_request.applied_at,
        created=new_leave_request.created,
    )


@app.patch("/leave-requests/{leave_request_id}/review", response_model=LeaveRequestResponse)
async def review_leave_request(
    leave_request_id: str,
    review: LeaveRequestReview,
    request: Request,
    db: Session = Depends(get_db),
):
    """Review (accept/reject) a leave request. Admin only."""
    require_admin(request.user.user_type)

    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == leave_request_id).first()
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")

    leave_request.is_accepted = review.is_accepted
    leave_request.reviewed_by = request.user.user_id
    leave_request.reviewed_at = datetime.now()
    db.commit()
    db.refresh(leave_request)

    return LeaveRequestResponse(
        id=str(leave_request.id),
        user_id=str(leave_request.user_id),
        organization_id=str(leave_request.organization_id),
        date=leave_request.date,
        leave_type=leave_request.leave_type,
        reason=leave_request.reason,
        is_accepted=leave_request.is_accepted,
        reviewed_by=str(leave_request.reviewed_by) if leave_request.reviewed_by else None,
        reviewed_at=leave_request.reviewed_at,
        applied_at=leave_request.applied_at,
        created=leave_request.created,
    )


@app.delete("/leave-requests/{leave_request_id}")
async def delete_leave_request(
    leave_request_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Delete a leave request. Users can delete their own, admins can delete any."""
    current_user = require_authenticated_user(request)

    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == leave_request_id).first()
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")

    # Regular users can only delete their own leave requests
    if (
        coerce_user_type(current_user.user_type) != UserType.ADMIN
        and str(leave_request.user_id) != current_user.user_id
    ):
        raise HTTPException(status_code=403, detail="Access denied")

    db.delete(leave_request)
    db.commit()
    return {"status": "ok", "message": "Leave request deleted"}


@app.delete("/admin/drop-leave-requests-db")
async def drop_leave_requests_db_table():
    drop_leave_requests_table()
    return {"status": "ok", "message": "Leave requests database table dropped"}
