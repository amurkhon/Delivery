
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from auth_routes import require_admin
from database import get_db
from models import User, UserRole
from schemas import UserModel, UserStatusUpdateModel
from fastapi_jwt_auth import AuthJWT
from libs.dtos.userdto import GetUsersInqueryParams, UserAdminUpdateModel, UserRoleUpdateModel


user_router = APIRouter(
    prefix='/user'
)

@user_router.get('/all/list', status_code=status.HTTP_200_OK, response_model=list[UserModel])
async def get_all_users(
    inquiry: GetUsersInqueryParams,
    Auth: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    print("Inquery params:", inquiry)
    require_admin(db, Auth)
    query = db.query(User)

    if inquiry.role is not None:
        query = query.filter(User.role == inquiry.role)
    if inquiry.is_active is not None:
        query = query.filter(User.is_active == inquiry.is_active)
    if inquiry.q:
        like = f"%{inquiry.q}%"
        query = query.filter((User.username.ilike(like)) | (User.email.ilike(like)))

    users = query.order_by(User.id.asc()).all()
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_staff": user.is_staff,  
            "is_active": user.is_active,
            "role": user.role,
        }
        for user in users
    ]


@user_router.get('/{user_id}', status_code=status.HTTP_200_OK, response_model=UserModel)
async def get_user_info(user_id: int, Auth: AuthJWT = Depends(), db: Session = Depends(get_db)):
    require_admin(db, Auth)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_staff": user.is_staff,  
        "is_active": user.is_active,
        "role": user.role,
    }


@user_router.patch('/{user_id}', status_code=status.HTTP_200_OK, response_model=UserModel)
async def update_user(
    user_id: int,
    payload: UserAdminUpdateModel,
    Auth: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    print("payload:", payload)
    admin_user = require_admin(db, Auth)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    
    print("Code passed here!", user.username)
    update_data = payload.dict(exclude_unset=True, exclude_none=True)
    print("update_data:", update_data)
    if not update_data:
        raise HTTPException(status_code=400, detail='No fields provided to update')

    if 'username' in update_data:
        username_exists = (
            db.query(User)
            .filter(User.username == update_data['username'], User.id != user_id)
            .first()
        )
        if username_exists:
            raise HTTPException(status_code=400, detail='Username already exists')

    if 'email' in update_data:
        email_exists = (
            db.query(User)
            .filter(User.email == update_data['email'], User.id != user_id)
            .first()
        )
        if email_exists:
            raise HTTPException(status_code=400, detail='Email already exists')

    if user.id == admin_user.id and 'is_staff' in update_data and update_data['is_staff'] is False:
        raise HTTPException(status_code=400, detail='Admin cannot remove own staff flag')

    for field, value in update_data.items():
        setattr(user, field, value)
    print("User updated:", user.username)

    user.updated_at = datetime.now()
    db.commit()
    db.refresh(user)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_staff": user.is_staff,  
        "is_active": user.is_active,
        "role": user.role,
    }


@user_router.patch('/{user_id}/role', status_code=status.HTTP_200_OK, response_model=UserModel)
async def update_user_role(
    user_id: int,
    payload: UserRoleUpdateModel,
    Auth: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    admin_user = require_admin(db, Auth)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')

    if user.id == admin_user.id and payload.role != user.role:
        raise HTTPException(status_code=400, detail='Admin cannot change own role')

    user.role = payload.role
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_staff": user.is_staff,  
        "is_active": user.is_active,
        "role": user.role,
    }


@user_router.patch('/{user_id}/status', status_code=status.HTTP_200_OK, response_model=UserModel)
async def update_user_status(
    user_id: int,
    payload: UserStatusUpdateModel,
    Auth: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    admin_user = require_admin(db, Auth)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')

    if user.id == admin_user.id and payload.is_active is False:
        raise HTTPException(status_code=400, detail='Admin cannot deactivate own account')

    user.is_active = payload.is_active
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_staff": user.is_staff,  
        "is_active": user.is_active,
        "role": user.role,
    }