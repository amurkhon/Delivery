from enum import Enum as PyEnum

from database import Base
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, Enum, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

class UserRole(str, PyEnum):
    admin = "admin"
    member = "member"
    staff = "staff"
    
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    is_active = Column(Boolean, default=True)
    is_staff = Column(Boolean, default=False)
    orders = relationship('Order', back_populates='user') # one to many relationship
    role = Column(Enum(UserRole, name="userrole"), default=UserRole.member, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<User {self.username}>"

class OrderStatus(str, PyEnum):
    pending = "pending"
    confirmed = "confirmed"
    delivered = "delivered"
    cancelled = "cancelled"

class ProductCategory(str, PyEnum):
    food = "food"
    drink = "drink"
    other = "other"

class Volume(str, PyEnum):
    small = "small"
    medium = "medium"
    large = "large"

order_products = Table(
    'order_products',
    Base.metadata,
    Column('order_id', ForeignKey('orders.id'), primary_key=True),
    Column('product_id', ForeignKey('products.id'), primary_key=True),
)


class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='orders') # many to one relationship
    order_date = Column(DateTime, default=func.now())
    quantity = Column(Integer, nullable=False)
    total_amount = Column(Float)
    status = Column(Enum(OrderStatus), default=OrderStatus.pending, nullable=False)
    products = relationship(
        'Product',
        secondary=order_products,
        back_populates='orders',
    ) # many to many relationship
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Order {self.id}>"

class ProductStatus(str, PyEnum):
    available = "available"
    unavailable = "unavailable"
    deleted = "deleted"

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    volume = Column(Enum(Volume, name="volume"), default=Volume.small, nullable=False)
    product_category = Column(Enum(ProductCategory, name="productcategory"), default=ProductCategory.other, nullable=False)
    status = Column(Enum(ProductStatus, name="productstatus"), default=ProductStatus.available, nullable=False)
    orders = relationship(
        'Order',
        secondary=order_products,
        back_populates='products',
    ) # many to many relationship
    images = relationship('ProductImage', back_populates='product', cascade='all, delete-orphan')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Product {self.name}>"


class ProductImage(Base):
    __tablename__ = 'product_images'
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now())
    product = relationship('Product', back_populates='images')

    def __repr__(self):
        return f"<ProductImage {self.id} product_id={self.product_id}>"
