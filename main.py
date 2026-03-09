from pathlib import Path
import os

from contextlib import asynccontextmanager
from alembic.config import Config
from alembic import command
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from auth_routes import auth_router
from orders_routes import order_router
from fastapi_jwt_auth import AuthJWT
from products_routes import product_router
from schemas import SignInModel, Token
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS, IS_PRODUCTION, UPLOAD_DIR, validate_production_config
from database import engine

def run_migrations():
    if os.getenv("SKIP_MIGRATIONS"):
        return
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


def ensure_upload_dir():
    path = Path(UPLOAD_DIR)
    if not path.is_absolute():
        path = Path.cwd() / path
    path.mkdir(parents=True, exist_ok=True)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        if IS_PRODUCTION:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_production_config()
    run_migrations()
    ensure_upload_dir()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@AuthJWT.load_config
def get_config():
    return Token()

app.include_router(auth_router)
app.include_router(order_router)
app.include_router(product_router)

ensure_upload_dir()
upload_path = Path(UPLOAD_DIR) if Path(UPLOAD_DIR).is_absolute() else Path.cwd() / UPLOAD_DIR
app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/health/ready")
async def health_ready():
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "detail": "Database unreachable"},
        )
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"message": "This is home page"}


@app.get("/page")
async def greet():
    return {"message": "Welcome to my page!"}

