# The Vault — Luxury Handbag Rentals API

Backend API for The Vault, a luxury designer handbag rental platform.

## Tech Stack

- **Python 3.11+** / **FastAPI** (async-capable REST framework)
- **SQLAlchemy 2.0** ORM (PostgreSQL-compatible, SQLite for dev)
- **JWT** authentication via `python-jose` + `passlib`
- **Stripe** payment processing
- **Pydantic** request/response validation

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env
# Edit .env with your settings (Stripe keys optional for dev)

# Run the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.
Interactive docs at `http://localhost:8000/docs` (Swagger UI).

## Seed Data

To populate with demo data (admin user, test user, 12 luxury bags):

```bash
python -c "from app.utils.seed import seed_database; seed_database()"
```

**Default accounts:**
- Admin: `admin@thevault.com` / `admin123!`
- Test user: `test@thevault.com` / `test123!`

## Project Structure

```
the-vault-api/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Environment configuration
│   ├── database.py          # DB engine, session, base model
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── user.py          # User & identity verification
│   │   ├── inventory.py     # Bag catalog & images
│   │   ├── booking.py       # Reservations & lifecycle
│   │   └── payment.py       # Payments & waitlist
│   ├── schemas/             # Pydantic request/response models
│   ├── routers/             # API endpoint handlers
│   │   ├── auth.py          # POST /auth/register, /auth/login
│   │   ├── users.py         # Profile, verification
│   │   ├── inventory.py     # Bag catalog CRUD
│   │   ├── bookings.py      # Booking creation & management
│   │   ├── payments.py      # Stripe PaymentIntent creation
│   │   ├── waitlist.py      # Waitlist for unavailable bags
│   │   ├── admin.py         # Admin dashboard & overview
│   │   └── webhooks.py      # Stripe webhook handler
│   ├── services/            # Business logic layer
│   │   ├── auth_service.py
│   │   ├── inventory_service.py
│   │   ├── booking_service.py
│   │   └── stripe_service.py
│   └── utils/
│       ├── security.py      # JWT, password hashing, auth deps
│       └── seed.py          # Database seeder
├── .env.example             # Environment template
├── requirements.txt
└── README.md
```

## API Endpoints

### Authentication
| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/auth/register` | Register new user | No |
| POST | `/auth/login` | Login, get JWT | No |
| GET | `/auth/me` | Get current user | JWT |

### Users & Verification
| Method | Path | Description | Auth |
|--------|------|-------------|------|
| PUT | `/users/me` | Update profile | JWT |
| POST | `/users/verifications` | Submit ID verification | JWT |
| GET | `/users/verifications` | List verification status | JWT |
| PUT | `/users/verifications/{id}/approve` | Approve verification | Admin |
| PUT | `/users/verifications/{id}/reject` | Reject verification | Admin |

### Inventory / Catalog
| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/inventory` | List & search bags | No |
| GET | `/inventory/brands` | Get all brands | No |
| GET | `/inventory/categories` | Get all categories | No |
| GET | `/inventory/{id}` | Bag details | No |
| POST | `/inventory` | Create bag listing | Admin |
| PUT | `/inventory/{id}` | Update bag | Admin |
| DELETE | `/inventory/{id}` | Soft-delete bag | Admin |
| POST | `/inventory/{id}/images` | Add image | Admin |
| DELETE | `/inventory/{id}/images/{img_id}` | Delete image | Admin |

### Bookings
| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/bookings` | Create booking | Verified |
| GET | `/bookings` | My bookings | JWT |
| GET | `/bookings/{id}` | Booking details | JWT/Admin |
| POST | `/bookings/{id}/cancel` | Cancel booking | JWT |
| POST | `/bookings/availability` | Check availability | No |
| GET | `/bookings/admin/all` | All bookings | Admin |
| PUT | `/bookings/{id}/status` | Update status | Admin |

### Payments
| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/payments/create-intent` | Create Stripe PaymentIntent | JWT |
| GET | `/payments` | My payments | JWT |
| GET | `/payments/{id}` | Payment details | JWT/Admin |

### Waitlist
| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/waitlist` | Join waitlist for a bag | JWT |
| GET | `/waitlist` | My waitlist entries | JWT |
| DELETE | `/waitlist/{id}` | Leave waitlist | JWT |
| GET | `/waitlist/admin/all` | All waitlist entries | Admin |

### Webhooks
| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/webhooks/stripe` | Stripe events | Stripe-Signature |

### Admin Dashboard
| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/admin/dashboard` | Stats & KPIs | Admin |
| GET | `/admin/users` | All users | Admin |
| GET | `/admin/revenue-overview` | Revenue breakdown | Admin |

## Authentication

All protected endpoints require a Bearer JWT token:

```
Authorization: Bearer <token>
```

Tokens are obtained via `POST /auth/register` or `POST /auth/login`.

## Future Considerations

- PostgreSQL migration for production
- Rate limiting
- Email notifications (via SendGrid/SES)
- Push notification integration for mobile app
- Bag availability calendar
- Image upload via S3/CDN
- Enhanced fraud detection
- Peak/holiday surge pricing engine