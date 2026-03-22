import datetime
from sqlalchemy.sql._elements_constructors import or_
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, status, Response
from fastapi_jwt_auth import AuthJWT
from schemas import SignInModel, SignUpModel
from database import get_db
from models import User, UserRole
from fastapi import HTTPException
import bcrypt
from fastapi.encoders import jsonable_encoder

auth_router = APIRouter(
    prefix='/auth'
)

def normalize_password(password: str | bytes) -> bytes | None:
    if not password:
        return None
    password_bytes = password.encode("utf-8") if isinstance(password, str) else password
    if len(password_bytes) > 72:
        return password_bytes[:72]
    return password_bytes

def hash_password(password: str | bytes) -> str:
    password_bytes = normalize_password(password)
    if not password_bytes:
        raise ValueError("Password is required")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    try:
        password_bytes = normalize_password(plain_password)
        if not password_bytes:
            return False
        hashed_bytes = (
            hashed_password.encode("utf-8")
            if isinstance(hashed_password, str)
            else hashed_password
        )
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except ValueError:
        return False

def get_current_user(db: Session, Authorize: AuthJWT) -> User:
    """Helper to get current authenticated user"""
    try:
        Authorize.jwt_required()
    except Exception:
        raise HTTPException(status_code=401, detail='Unauthorized')
    current_username = Authorize.get_jwt_subject()
    user = db.query(User).filter(User.username == current_username).first()
    if not user:
        raise HTTPException(status_code=401, detail='User not found')
    return user

def require_admin(db: Session, Authorize: AuthJWT) -> User:
    """Helper to require admin role"""
    user = get_current_user(db, Authorize)
    if user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail='Admin access required')
    return user

@auth_router.get('/')
async def auth_home(Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    get_current_user(db, Authorize)
    return {'message': 'This is auth route signup page!'}

@auth_router.post('/signup', status_code=status.HTTP_201_CREATED)
async def signup(user: SignUpModel, db: Session = Depends(get_db)):
    if user.confirm_password is not None and user.password != user.confirm_password:
        raise HTTPException(status_code=400, detail='Passwords do not match')
    user_exists = db.query(User).filter(User.email == user.email).first()
    if user_exists:
        raise HTTPException(status_code=400, detail='User already exists')
    
    # Validate role
    try:
        role = UserRole(user.role) if user.role else UserRole.member
    except ValueError:
        raise HTTPException(status_code=400, detail='Invalid role. Must be "admin", "member", or "staff"')
    
    new_user = User(
        username=user.username, 
        email=user.email, 
        password=hash_password(user.password),
        role=role,
        is_active=user.is_active,
        is_staff=user.is_staff,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    response = {
        'id': new_user.id,
        'username': new_user.username,
        'email': new_user.email,
        'role': new_user.role.value,
        'is_active': new_user.is_active,
        'is_staff': new_user.is_staff,
        'created_at': new_user.created_at,
        'updated_at': new_user.updated_at,
    }
    return response

@auth_router.post('/signin', status_code=status.HTTP_200_OK)
async def signin(user: SignInModel, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    access_lifetime = datetime.timedelta(hours=24)
    refresh_lifetime = datetime.timedelta(days=30)

    user_exists = db.query(User).filter(
        or_(
            User.username == user.username_or_email,
            User.email == user.username_or_email,
        )
    ).first()
    if not user_exists:
        raise HTTPException(status_code=400, detail='Invalid username or email!')

    if user_exists and verify_password(user.password, user_exists.password):
        access_token = Authorize.create_access_token(subject=user_exists.username, expires_time=access_lifetime)
        refresh_token = Authorize.create_refresh_token(subject=user_exists.username, expires_time=refresh_lifetime)
        token = {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
        response = {
            "user": user_exists, 
            "token": token
            }
        Authorize.set_access_cookies(access_token)
        Authorize.set_refresh_cookies(refresh_token)
        return jsonable_encoder(response)
    raise HTTPException(status_code=400, detail='Invalid email or password')

@auth_router.post('/logout', status_code=status.HTTP_200_OK)
async def logout(response: Response, Authorize: AuthJWT = Depends()):
    """Logout user by unsetting JWT cookies"""
    Authorize.unset_jwt_cookies()
    return {"success": True, "message": "Successfully logged out"}

@auth_router.get('/signin/refresh')
async def refresh_token(Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    try:
        access_lifetime = datetime.timedelta(minutes=15)
        refresh_lifetime = datetime.timedelta(days=30)

        Authorize.jwt_refresh_token_required()
        current_user = Authorize.get_jwt_subject()

        user = db.query(User).filter(User.username == current_user).first()
        if not user:
            raise HTTPException(status_code=400, detail='Invalid user')
        access_token = Authorize.create_access_token(subject=user.username, expires_time=access_lifetime)
        refresh_token = Authorize.create_refresh_token(subject=user.username, expires_time=refresh_lifetime)
        token = {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
        response = {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "message": "Successfully refreshed token",
            "token": token,
        }
        Authorize.set_access_cookies(access_token)
        Authorize.set_refresh_cookies(refresh_token)
        return jsonable_encoder(response)
    except Exception:
        raise HTTPException(status_code=401, detail='Invalid refresh token')
