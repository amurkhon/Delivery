#!/bin/bash
# Production start script - run with: ./scripts/start.sh
# Ensure .env is loaded (e.g. via export or source)
exec gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
