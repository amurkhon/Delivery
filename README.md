# Delivery API

FastAPI backend for the Delivery app - products, orders, authentication, and product image uploads.

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Copy env template and configure
cp .env.example .env

# Run migrations
alembic upgrade head

# Start dev server
uvicorn main:app --reload
```

## Production Deployment

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ENVIRONMENT` | No | `development` or `production` (default: development) |
| `DATABASE_URL` | Yes (prod) | PostgreSQL connection string |
| `JWT_SECRET_KEY` | Yes (prod) | Strong secret, 32+ chars. Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `CORS_ORIGINS` | No | Comma-separated allowed origins (default: localhost) |
| `UPLOAD_DIR` | No | Upload directory (default: uploads) |
| `MAX_IMAGE_SIZE_MB` | No | Max image size in MB (default: 5) |
| `LOG_LEVEL` | No | DEBUG, INFO, WARNING, ERROR |

### Running with Gunicorn

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

Or use the start script (load .env first):

```bash
source .env  # or export variables
./scripts/start.sh
```

### Docker

```bash
# Build and run with Docker Compose
docker-compose up -d

# Set JWT_SECRET_KEY and CORS_ORIGINS in .env or export before running
export JWT_SECRET_KEY=iu3tg6438gr8cx71987ruy1498ruy2498ruy2498ruy
docker-compose up -d
```

### Health Endpoints

- `GET /health` - Liveness probe (returns 200)
- `GET /health/ready` - Readiness probe (checks DB, returns 503 if unreachable)

### Pre-Launch Checklist

- [ ] `JWT_SECRET_KEY` is strong and unique (32+ chars)
- [ ] `DATABASE_URL` points to production database
- [ ] `CORS_ORIGINS` includes only trusted frontend URLs
- [ ] `uploads/` directory is persisted (volume or object storage)
- [ ] HTTPS is configured (reverse proxy or PaaS)
