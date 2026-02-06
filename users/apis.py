from datetime import datetime

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from application.app import app
from auth.passwords import hash_password
from database.db import drop_users_table, get_db
from users.choices import UserType
from users.models import User, UserItem, UserRequest, UserResponse, UsersListResponse


def _coerce_user_type(value: str) -> UserType:
    normalized = value.strip().upper()
    try:
        return UserType[normalized]
    except KeyError:
        raise HTTPException(status_code=403, detail="Admin access required")


def _require_admin(user_type: str) -> None:
    if _coerce_user_type(user_type) != UserType.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")


def _require_authenticated_user(request: Request):
    if not request.user or not request.user.is_authenticated:
        raise HTTPException(status_code=401, detail="Authentication required")
    return request.user


@app.get("/users", response_model=UsersListResponse)
async def get_users(
    request: Request,
    db: Session = Depends(get_db),
):
    _require_admin(request.user.user_type)
    rows = db.query(User).order_by(User.created_at.desc()).all()
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
    current_user = _require_authenticated_user(request)
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
        created_at=datetime.now(),
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
