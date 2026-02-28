import os
from pathlib import Path

from contextlib import asynccontextmanager
from alembic.config import Config
from alembic import command
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from auth_routes import auth_router
from orders_routes import order_router
from fastapi_jwt_auth import AuthJWT
from products_routes import product_router
from schemas import SignInModel, Token
from fastapi.middleware.cors import CORSMiddleware

def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


def ensure_upload_dir():
    upload_dir = os.getenv("UPLOAD_DIR", "uploads")
    path = Path(upload_dir)
    if not path.is_absolute():
        path = Path.cwd() / path
    path.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    ensure_upload_dir()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
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
upload_dir = os.getenv("UPLOAD_DIR", "uploads")
upload_path = Path(upload_dir) if Path(upload_dir).is_absolute() else Path.cwd() / upload_dir
app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")

@app.get("/")
async def root():
    return {"message": "This is home page"}

@app.get("/page")
async def greet():
    return {"message": "Welcome to my page!"}

