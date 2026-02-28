from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, File, UploadFile, status, Query
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from fastapi_jwt_auth import AuthJWT
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from database import get_db
from models import Product, ProductImage, ProductStatus, UserRole
from schemas import ProductDeleteModel, ProductImageResponse, ProductModel
from auth_routes import get_current_user, require_admin
from services.image_service import (
    build_image_url,
    delete_image as svc_delete_image,
    save_upload,
    set_primary as svc_set_primary,
)

product_router = APIRouter(
    prefix='/product'
)


def _product_with_images(product: Product) -> dict:
    """Build product dict with image URLs for response."""
    data = jsonable_encoder(product)
    if hasattr(product, "images") and product.images is not None:
        data["images"] = [
            ProductImageResponse(
                id=img.id,
                product_id=img.product_id,
                url=build_image_url(img.filename),
                is_primary=img.is_primary,
                sort_order=img.sort_order,
            )
            for img in sorted(product.images, key=lambda x: (not x.is_primary, x.sort_order))
        ]
    else:
        data["images"] = []
    return data

@product_router.post('/create', status_code=status.HTTP_201_CREATED, response_model=ProductModel)
async def create_product(product: ProductModel, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    # Only admin can create products
    require_admin(db, Authorize)
    
    new_product = Product(
        name=product.name, 
        price=product.price, 
        volume=product.volume, 
        product_category=product.product_category,
        status=product.status or ProductStatus.available,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    return _product_with_images(new_product)

@product_router.put('/update/{product_id}', status_code=status.HTTP_200_OK, response_model=ProductModel)
async def update_product(product_id: int, product: ProductModel, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    # Only admin can update products
    require_admin(db, Authorize)
    
    target_product = db.query(Product).filter(Product.id == product_id).first()
    if not target_product:
        raise HTTPException(status_code=404, detail='Product not found')
    
    target_product.name = product.name
    target_product.price = product.price
    target_product.volume = product.volume
    target_product.product_category = product.product_category
    target_product.updated_at = datetime.now()
    
    db.commit()
    db.refresh(target_product)
    
    return _product_with_images(target_product)

@product_router.get('/single/{product_id}', status_code=status.HTTP_200_OK, response_model=ProductModel)
async def get_product(product_id: int, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    get_current_user(db, Authorize)
    
    target_product = (
        db.query(Product)
        .options(joinedload(Product.images))
        .filter(Product.id == product_id)
        .first()
    )
    if not target_product:
        raise HTTPException(status_code=404, detail='Product not found')
    
    return _product_with_images(target_product)

@product_router.delete('/delete/{product_id}', status_code=status.HTTP_200_OK, response_model=ProductModel)
async def delete_product(product_id: int, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    # Only admin can delete products
    require_admin(db, Authorize)
    
    target_product = db.query(Product).filter(Product.id == product_id).first()
    if not target_product:
        raise HTTPException(status_code=404, detail='Product not found')
    
    # Soft delete by setting status to deleted
    target_product.status = ProductStatus.deleted
    target_product.updated_at = datetime.now()
    
    db.commit()
    db.refresh(target_product)
    
    return _product_with_images(target_product)

@product_router.get('/all', status_code=status.HTTP_200_OK, response_model=List[ProductModel])
async def get_products(
    status_filter: Optional[ProductStatus] = Query(default=ProductStatus.available, alias="status"),
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db)
):
    get_current_user(db, Authorize)
    
    products = (
        db.query(Product)
        .options(joinedload(Product.images))
        .filter(Product.status == status_filter)
        .all()
    )
    if not products:
        return []
    
    return [_product_with_images(p) for p in products]


# Image endpoints
@product_router.post(
    '/{product_id}/images',
    status_code=status.HTTP_201_CREATED,
    response_model=List[ProductImageResponse],
)
async def upload_product_images(
    product_id: int,
    files: List[UploadFile] = File(...),
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    require_admin(db, Authorize)
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail='Product not found')

    count = db.query(ProductImage).filter(ProductImage.product_id == product_id).count()
    is_first = count == 0
    result = []
    for i, file in enumerate(files):
        product_image = save_upload(file, product_id, db, is_first=is_first, sort_order=count + i)
        result.append(
            ProductImageResponse(
                id=product_image.id,
                product_id=product_image.product_id,
                url=build_image_url(product_image.filename),
                is_primary=product_image.is_primary,
                sort_order=product_image.sort_order,
            )
        )
        if is_first:
            is_first = False
        count += 1
    return result


@product_router.get(
    '/{product_id}/images',
    status_code=status.HTTP_200_OK,
    response_model=List[ProductImageResponse],
)
async def list_product_images(
    product_id: int,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    get_current_user(db, Authorize)
    images = (
        db.query(ProductImage)
        .filter(ProductImage.product_id == product_id)
        .order_by(ProductImage.is_primary.desc(), ProductImage.sort_order)
        .all()
    )
    return [
        ProductImageResponse(
            id=img.id,
            product_id=img.product_id,
            url=build_image_url(img.filename),
            is_primary=img.is_primary,
            sort_order=img.sort_order,
        )
        for img in images
    ]


@product_router.delete(
    '/{product_id}/images/{image_id}',
    status_code=status.HTTP_200_OK,
)
async def delete_product_image(
    product_id: int,
    image_id: int,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    require_admin(db, Authorize)
    deleted = svc_delete_image(image_id, db)
    if not deleted or deleted.product_id != product_id:
        raise HTTPException(status_code=404, detail='Image not found')
    return {"success": True, "message": "Image deleted"}


@product_router.put(
    '/{product_id}/images/{image_id}/primary',
    status_code=status.HTTP_200_OK,
    response_model=ProductImageResponse,
)
async def set_product_image_primary(
    product_id: int,
    image_id: int,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    require_admin(db, Authorize)
    product_image = svc_set_primary(image_id, product_id, db)
    return ProductImageResponse(
        id=product_image.id,
        product_id=product_image.product_id,
        url=build_image_url(product_image.filename),
        is_primary=product_image.is_primary,
        sort_order=product_image.sort_order,
    )
