import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from models import Product, ProductImage

# Configuration (from env with defaults)
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MAX_IMAGE_SIZE_MB = int(os.getenv("MAX_IMAGE_SIZE_MB", "5"))
MAX_IMAGES_PER_PRODUCT = 10
THUMBNAIL_SIZE = (200, 200)
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


def _get_upload_base() -> Path:
    """Get base upload directory (resolved from cwd)."""
    base = Path(UPLOAD_DIR)
    if not base.is_absolute():
        base = Path.cwd() / base
    return base


def _ensure_upload_dir(product_id: int) -> Path:
    """Ensure product upload directory exists and return it."""
    base = _get_upload_base()
    product_dir = base / "products" / str(product_id)
    product_dir.mkdir(parents=True, exist_ok=True)
    return product_dir


def _validate_file(file: UploadFile) -> tuple[str, str]:
    """Validate file and return (extension, content_type). Raises HTTPException on invalid."""
    if not file.filename or ".." in file.filename or file.filename.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid filename")
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid extension. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )
    content_type = file.content_type or ""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type. Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}",
        )
    return ext, content_type


def _validate_size(file: UploadFile) -> None:
    """Validate file size. Raises HTTPException if too large."""
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    max_bytes = MAX_IMAGE_SIZE_MB * 1024 * 1024
    if size > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {MAX_IMAGE_SIZE_MB}MB",
        )


def save_upload(
    file: UploadFile,
    product_id: int,
    db: Session,
    is_first: bool = False,
    sort_order: int = 0,
) -> ProductImage:
    """Validate, save file, create thumbnail, and return ProductImage."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    count = db.query(ProductImage).filter(ProductImage.product_id == product_id).count()
    if count >= MAX_IMAGES_PER_PRODUCT:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_IMAGES_PER_PRODUCT} images per product",
        )

    ext, _ = _validate_file(file)
    _validate_size(file)

    product_dir = _ensure_upload_dir(product_id)
    unique_id = uuid.uuid4().hex[:12]
    base_name = f"{unique_id}.{ext}"
    thumb_name = f"{unique_id}_thumb.{ext}"
    full_path = product_dir / base_name
    thumb_path = product_dir / thumb_name

    # Save full image
    contents = file.file.read()
    with open(full_path, "wb") as f:
        f.write(contents)

    # Create thumbnail and strip EXIF
    try:
        img = Image.open(full_path)
        if img.mode in ("RGBA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "RGBA":
                background.paste(img, mask=img.split()[-1])
            else:
                background.paste(img)
            img = background
        else:
            img = img.convert("RGB")
        img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        img.save(thumb_path, "JPEG", quality=85)
    except Exception as e:
        if full_path.exists():
            full_path.unlink()
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")

    # Relative path for DB (e.g. products/1/abc123.jpg)
    rel_filename = f"products/{product_id}/{base_name}"

    is_primary = is_first or count == 0

    product_image = ProductImage(
        product_id=product_id,
        filename=rel_filename,
        original_filename=file.filename or base_name,
        is_primary=is_primary,
        sort_order=sort_order,
    )
    db.add(product_image)
    db.commit()
    db.refresh(product_image)
    return product_image


def delete_image(image_id: int, db: Session) -> Optional[ProductImage]:
    """Delete image record and associated files. Returns deleted ProductImage or None."""
    product_image = db.query(ProductImage).filter(ProductImage.id == image_id).first()
    if not product_image:
        return None

    base = _get_upload_base()
    full_path = base / product_image.filename
    # Thumbnail: products/1/abc.jpg -> products/1/abc_thumb.jpg (thumb saved as .jpg)
    parts = product_image.filename.rsplit(".", 1)
    thumb_filename = f"{parts[0]}_thumb.jpg" if len(parts) == 2 else f"{product_image.filename}_thumb"
    thumb_path = base / thumb_filename

    if full_path.exists():
        full_path.unlink()
    if thumb_path.exists():
        thumb_path.unlink()

    db.delete(product_image)
    db.commit()
    return product_image


def set_primary(image_id: int, product_id: int, db: Session) -> ProductImage:
    """Set image as primary; unset others for this product."""
    product_image = (
        db.query(ProductImage)
        .filter(ProductImage.id == image_id, ProductImage.product_id == product_id)
        .first()
    )
    if not product_image:
        raise HTTPException(status_code=404, detail="Image not found")

    db.query(ProductImage).filter(ProductImage.product_id == product_id).update(
        {"is_primary": False}
    )
    product_image.is_primary = True
    db.commit()
    db.refresh(product_image)
    return product_image


def build_image_url(filename: str, base_url: str = "/uploads") -> str:
    """Build full URL for an image from its stored filename."""
    return f"{base_url.rstrip('/')}/{filename}"
