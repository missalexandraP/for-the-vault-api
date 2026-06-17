"""The Vault — Luxury Handbag Rentals API

FastAPI application serving the backend for the luxury handbag rental platform.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import engine, Base
from app.services.stripe_service import StripeService
from app.utils.security_hardening import rate_limit_middleware

# Import routers — use fully-qualified imports to avoid name collisions with models
from app.routers import auth as auth_router_mod
from app.routers import users as users_router_mod
from app.routers import bookings as bookings_router_mod
from app.routers import payments as payments_router_mod
from app.routers import waitlist as waitlist_router_mod
from app.routers import admin as admin_router_mod
from app.routers import webhooks as webhooks_router_mod
from app.routers import inventory as inventory_router_mod
from app.routers import public as public_router_mod

# Import models so they register with SQLAlchemy metadata
import app.models.user  # noqa: F401
import app.models.inventory  # noqa: F401
import app.models.booking  # noqa: F401
import app.models.payment  # noqa: F401


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        description="Backend API for The Vault — Luxury Handbag Rentals",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware — restrictive in production, permissive in dev
    if settings.CORS_ORIGINS == "*":
        # Dev mode — allow all origins (mobile app needs this)
        origins = ["*"]
        allow_creds = True
    else:
        # Production — restrict to specific origins
        origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
        allow_creds = True

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=allow_creds,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With",
                       "Stripe-Signature", "X-API-Key"],
        expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "Retry-After"],
        max_age=600,
    )

    # Rate limiting middleware
    app.middleware("http")(rate_limit_middleware)

    # Initialize Stripe
    StripeService.initialize()

    # Register routers — public router first so root route is registered
    app.include_router(public_router_mod.router)
    app.include_router(auth_router_mod.router)
    app.include_router(users_router_mod.router)
    app.include_router(inventory_router_mod.router)
    app.include_router(bookings_router_mod.router)
    app.include_router(payments_router_mod.router)
    app.include_router(waitlist_router_mod.router)
    app.include_router(webhooks_router_mod.router)
    app.include_router(admin_router_mod.router)

    # Mount static files for any additional assets (images, etc.)
    try:
        app.mount("/static", StaticFiles(directory="app/static"), name="static")
    except Exception:
        pass  # Static directory may not exist yet

    # Health check
    @app.get("/health", tags=["System"])
    def health_check():
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": "1.0.0",
        }

    return app


app = create_application()


@app.on_event("startup")
def on_startup():
    """Create database tables on startup."""
    Base.metadata.create_all(bind=engine)
    print(f"✓ {settings.APP_NAME} API is ready")
    print(f"✓ Database tables created")
    print(f"✓ Documentation at /docs")


# For running directly with `python app/main.py`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)