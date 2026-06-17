# The Vault — Docker Deployment

## Prerequisites
- Docker and Docker Compose installed
- `.env` file configured with production values

## Quick Start

```bash
# Build and start
docker-compose up --build -d

# Check logs
docker-compose logs -f api

# Seed the database (first time only)
docker-compose exec api python -c "from app.utils.seed import seed_database; seed_database()"

# Stop
docker-compose down
```

## Environment Variables for Production
Set these in `.env` before deploying:

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | JWT signing key | Yes |
| `DATABASE_URL` | Database connection string | Yes |
| `STRIPE_SECRET_KEY` | Stripe API secret | For payments |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | For webhooks |
| `SMTP_HOST` | SMTP server hostname | For emails |
| `SMTP_USER` | SMTP username | For emails |
| `SMTP_PASSWORD` | SMTP password | For emails |
| `APP_URL` | Public app URL | For email links |
| `DEBUG` | Set to `false` in production | Yes |

## Production Considerations
1. Use PostgreSQL instead of SQLite for production
2. Set up a reverse proxy (nginx/Caddy) for TLS termination
3. Configure proper CORS origins
4. Use secrets management for sensitive values
5. Set up health checks and monitoring