"""Seed data for development and demo environments."""

from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.user import User
from app.models.inventory import Bag, BagImage
from app.utils.security import hash_password


def seed_database():
    """Populate the database with initial data for development."""
    # Ensure tables exist
    from app.database import engine, Base
    from app.models import user, inventory, booking, payment  # noqa: F401
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(User).count() > 0:
            print("Database already has data, skipping seed.")
            return

        # --- Admin user ---
        admin = User(
            email="admin@thevault.com",
            full_name="Vault Admin",
            password_hash=hash_password("admin123!"),
            is_admin=True,
            is_verified=True,
            is_active=True,
        )
        db.add(admin)

        # --- Test user ---
        test_user = User(
            email="test@thevault.com",
            full_name="Test User",
            password_hash=hash_password("test123!"),
            is_verified=True,
            is_active=True,
        )
        db.add(test_user)
        db.flush()

        # --- Luxury Bag Inventory ---

        bags_data = [
            {
                "brand": "Hermès",
                "model": "Birkin 30",
                "category": "tote",
                "description": "The iconic Hermès Birkin 30 in Togo leather. Features signature turn-lock closure, double handles, and palladium hardware. A timeless investment piece that epitomizes luxury craftsmanship.",
                "color": "Black",
                "material": "Togo Leather",
                "market_value": 12000.00,
                "rental_price_per_day": 150.00,
                "deposit_amount": 3000.00,
                "condition": "excellent",
                "year": 2023,
                "is_featured": True,
                "stock_quantity": 1,
            },
            {
                "brand": "Chanel",
                "model": "Classic Flap Bag Medium",
                "category": "crossbody",
                "description": "The legendary Chanel Classic Flap in caviar leather with gold-tone hardware. Features the iconic CC turn-lock closure and interwoven chain strap. A true fashion house staple.",
                "color": "Beige",
                "material": "Caviar Leather",
                "market_value": 8800.00,
                "rental_price_per_day": 110.00,
                "deposit_amount": 2200.00,
                "condition": "excellent",
                "year": 2024,
                "is_featured": True,
                "stock_quantity": 2,
            },
            {
                "brand": "Dior",
                "model": "Lady Dior Medium",
                "category": "shoulder",
                "description": "The elegant Lady Dior in lambskin leather with cannage stitching. Features the iconic D.I.O.R. charms and removable chain strap. Princess Diana's favorite bag.",
                "color": "Powder Pink",
                "material": "Lambskin Leather",
                "market_value": 6500.00,
                "rental_price_per_day": 85.00,
                "deposit_amount": 1600.00,
                "condition": "excellent",
                "year": 2024,
                "is_featured": True,
                "stock_quantity": 1,
            },
            {
                "brand": "Louis Vuitton",
                "model": "Neverfull MM",
                "category": "tote",
                "description": "The iconic Louis Vuitton Neverfull in Damier Ebene canvas. Spacious interior with side laces for adjustable silhouette. Perfect everyday luxury tote.",
                "color": "Brown",
                "material": "Coated Canvas",
                "market_value": 2100.00,
                "rental_price_per_day": 35.00,
                "deposit_amount": 500.00,
                "condition": "excellent",
                "year": 2023,
                "is_featured": False,
                "stock_quantity": 3,
            },
            {
                "brand": "Gucci",
                "model": "Jackie 1961 Small",
                "category": "crossbody",
                "description": "The revived Gucci Jackie 1961 in smooth leather with the iconic piston closure and web stripe. A vintage-inspired silhouette reimagined for modern wardrobes.",
                "color": "White",
                "material": "Smooth Leather",
                "market_value": 2800.00,
                "rental_price_per_day": 55.00,
                "deposit_amount": 700.00,
                "condition": "excellent",
                "year": 2024,
                "is_featured": False,
                "stock_quantity": 2,
            },
            {
                "brand": "Celine",
                "model": "Triomphe Medium",
                "category": "shoulder",
                "description": "The Celine Triomphe in shiny calfskin leather with the iconic Triomphe clasp. Clean lines and minimalist elegance define this modern classic.",
                "color": "Tan",
                "material": "Calfskin Leather",
                "market_value": 3900.00,
                "rental_price_per_day": 65.00,
                "deposit_amount": 1000.00,
                "condition": "excellent",
                "year": 2023,
                "is_featured": True,
                "stock_quantity": 1,
            },
            {
                "brand": "Saint Laurent",
                "model": "Le 5 à 7 Small",
                "category": "hobo",
                "description": "The Saint Laurent Le 5 à 7 in textured leather with the iconic Cassandre logo. Slouchy hobo silhouette with an adjustable leather strap.",
                "color": "Black",
                "material": "Grained Leather",
                "market_value": 2450.00,
                "rental_price_per_day": 45.00,
                "deposit_amount": 600.00,
                "condition": "excellent",
                "year": 2024,
                "is_featured": False,
                "stock_quantity": 2,
            },
            {
                "brand": "Bottega Veneta",
                "model": "Jodie Mini",
                "category": "hobo",
                "description": "The iconic Bottega Veneta Jodie in the signature Intrecciato woven leather. The distinctive curved hobo shape with a knotted handle makes this a modern status symbol.",
                "color": "Parakeet Green",
                "material": "Intrecciato Nappa",
                "market_value": 3200.00,
                "rental_price_per_day": 60.00,
                "deposit_amount": 800.00,
                "condition": "excellent",
                "year": 2024,
                "is_featured": True,
                "stock_quantity": 1,
            },
            {
                "brand": "Prada",
                "model": "Galleria Saffiano Medium",
                "category": "satchel",
                "description": "The timeless Prada Galleria in Saffiano leather with enamel metal triangle logo. Structured satchel design with double handles and detachable shoulder strap.",
                "color": "Navy",
                "material": "Saffiano Leather",
                "market_value": 2900.00,
                "rental_price_per_day": 50.00,
                "deposit_amount": 750.00,
                "condition": "excellent",
                "year": 2023,
                "is_featured": False,
                "stock_quantity": 2,
            },
            {
                "brand": "Hermès",
                "model": "Kelly 28 Retourne",
                "category": "shoulder",
                "description": "The Hermès Kelly 28 in Epsom leather with palladium hardware. Features a single handle, detachable shoulder strap, and the iconic turn-lock closure. Handcrafted in France.",
                "color": "Gold",
                "material": "Epsom Leather",
                "market_value": 14500.00,
                "rental_price_per_day": 200.00,
                "deposit_amount": 3500.00,
                "condition": "excellent",
                "year": 2023,
                "is_featured": True,
                "stock_quantity": 1,
            },
            {
                "brand": "Fendi",
                "model": "Baguette Medium",
                "category": "shoulder",
                "description": "The iconic Fendi Baguette in canvas with FF motif and leather trim. The original 'It bag' reimagined with the signature Fendi Roma clasp. Detachable shoulder strap.",
                "color": "Brown/Beige",
                "material": "Canvas/Leather",
                "market_value": 3200.00,
                "rental_price_per_day": 55.00,
                "deposit_amount": 800.00,
                "condition": "excellent",
                "year": 2024,
                "is_featured": False,
                "stock_quantity": 1,
            },
            {
                "brand": "Chanel",
                "model": "Boy Chanel Old Medium",
                "category": "crossbody",
                "description": "The Chanel Boy in aged calfskin leather with ruthenium hardware. Features the signature rectangular CC turn-lock and chunky chain strap. Edgy and sophisticated.",
                "color": "Dark Grey",
                "material": "Aged Calfskin",
                "market_value": 6200.00,
                "rental_price_per_day": 95.00,
                "deposit_amount": 1500.00,
                "condition": "excellent",
                "year": 2023,
                "is_featured": False,
                "stock_quantity": 1,
            },
        ]

        for bag_data in bags_data:
            bag = Bag(**bag_data)
            db.add(bag)

        db.commit()
        print(f"Seed complete: 1 admin user, 1 test user, {len(bags_data)} luxury bags created.")

    finally:
        db.close()