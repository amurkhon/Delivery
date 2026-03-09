#!/bin/bash
set -e

echo "Creating base tables and stamping migrations..."
python -c "
from database import engine, Base
from models import User, Order, Product
from alembic.config import Config
from alembic import command
from sqlalchemy import inspect

# Check if tables exist
inspector = inspect(engine)
tables_exist = 'users' in inspector.get_table_names()

# Create all tables (idempotent)
Base.metadata.create_all(bind=engine)

alembic_cfg = Config('alembic.ini')

if not tables_exist:
    # Fresh DB - tables just created with current schema, stamp to head
    print('Fresh database - stamping to head...')
    command.stamp(alembic_cfg, 'head')
else:
    # Existing DB - run any pending migrations
    print('Existing database - running migrations...')
    command.upgrade(alembic_cfg, 'head')

print('Database ready.')
"

echo "Starting gunicorn..."
export SKIP_MIGRATIONS=1
exec gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
