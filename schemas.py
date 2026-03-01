from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

from config import JWT_SECRET_KEY
from models import ProductCategory, ProductStatus, UserRole, OrderStatus, Volume

class SignUpModel(BaseModel):
    id: Optional[int] = None
    username: str
    email: str
    password: str
    confirm_password: str
    is_staff: Optional[bool] = False
    is_active: Optional[bool] = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    role: Optional[str] = "member"

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "username": "amir",
                "email": "amir@gmail.com",
                "password": "123456",
                "confirm_password": "123456",
                "is_staff": False,
                "is_active": True,
                "role": "member",
            }
        },
    )

class SignInModel(BaseModel):
    username_or_email: str
    password: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "username_or_email": "amir@gmail.com",
                "password": "123456",
            }
        },
    )

class Token(BaseModel):
    authjwt_secret_key: str = JWT_SECRET_KEY
    authjwt_token_location: set = {"cookies"}
    authjwt_cookie_csrf_protect: bool = False

# Order schemas
class OrderCreateModel(BaseModel):
    """Schema for creating a new order with multiple products"""
    product_ids: List[int]

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "product_ids": [1, 2, 3],
            }
        }

class OrderModel(BaseModel):
    id: Optional[int] = None
    quantity: Optional[int] = None
    user_id: Optional[int] = None
    total_amount: Optional[float] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "quantity": 3,
                "user_id": 1,
                "total_amount": 150.00,
                "status": "pending",
            }
        }

class OrderUpdateModel(BaseModel):
    status: OrderStatus

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "status": "confirmed",
            }
        }

# Product schemas
class ProductImageResponse(BaseModel):
    id: int
    product_id: int
    url: str
    is_primary: bool
    sort_order: int

    class Config:
        from_attributes = True


class ProductModel(BaseModel):
    id: Optional[int] = None
    name: str
    price: float
    volume: Volume
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: Optional[ProductStatus] = ProductStatus.available
    product_category: ProductCategory
    images: Optional[List["ProductImageResponse"]] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "name": "Product 1",
                "price": 100.00,
                "volume": "small",
                "status": "available",
                "product_category": "food",
            }
        }

class ProductDeleteModel(BaseModel):
    status: ProductStatus

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "status": "deleted",
            }
        }

class ProductInquiryModel(BaseModel):
    status: Optional[ProductStatus] = ProductStatus.available

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "status": "available"
            }
        }
