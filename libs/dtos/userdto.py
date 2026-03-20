from typing import Optional

from fastapi import Query
from pydantic import BaseModel, root_validator

from models import UserRole


class GetUsersInqueryParams(BaseModel):
    role: UserRole | None = Query(default="member")
    is_active: bool | None = Query(default=True)
    q: Optional[str] = Query(default=None, description='Search by username or email')

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "role": "member",
                "is_active": True,
                "q": "search term",
            }
        }


class UserAdminUpdateModel(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    is_staff: Optional[bool] = None

    class Config:
        orm_mode = True
        extra = "forbid"
        schema_extra = {
            "example": {
                "username": "amir_updated",
                "email": "amir_updated@gmail.com",
                "is_staff": True,
            }
        }

    @root_validator
    def validate_has_at_least_one_field(cls, values):
        if values.get("username") is None and values.get("email") is None and values.get("is_staff") is None:
            raise ValueError("At least one field is required: username, email, is_staff")
        return values


class UserRoleUpdateModel(BaseModel):
    role: UserRole

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "role": "member",
            }
        }