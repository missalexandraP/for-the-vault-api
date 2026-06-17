"""Inventory catalog service — CRUD for bags and images."""

from typing import Optional, List
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.inventory import Bag, BagImage


class InventoryService:
    @staticmethod
    def create_bag(db: Session, data: dict) -> Bag:
        """Create a new bag listing."""
        bag = Bag(**data)
        db.add(bag)
        db.commit()
        db.refresh(bag)
        return bag

    @staticmethod
    def get_bag(db: Session, bag_id: str) -> Bag:
        """Get a single bag by ID."""
        bag = db.query(Bag).filter(Bag.id == bag_id).first()
        if not bag:
            raise HTTPException(status_code=404, detail="Bag not found")
        return bag

    @staticmethod
    def list_bags(
        db: Session,
        brand: Optional[str] = None,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        is_available: Optional[bool] = None,
        is_featured: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        include_inactive: bool = False,
    ) -> dict:
        """List bags with filtering, search, and pagination."""
        query = db.query(Bag)

        if not include_inactive:
            query = query.filter(Bag.is_active == True)

        if brand:
            query = query.filter(Bag.brand.ilike(f"%{brand}%"))
        if category:
            query = query.filter(Bag.category == category)
        if min_price is not None:
            query = query.filter(Bag.rental_price_per_day >= min_price)
        if max_price is not None:
            query = query.filter(Bag.rental_price_per_day <= max_price)
        if is_available is not None:
            query = query.filter(Bag.is_available == is_available)
        if is_featured is not None:
            query = query.filter(Bag.is_featured == is_featured)
        if search:
            query = query.filter(
                or_(
                    Bag.brand.ilike(f"%{search}%"),
                    Bag.model.ilike(f"%{search}%"),
                    Bag.description.ilike(f"%{search}%"),
                    Bag.color.ilike(f"%{search}%"),
                )
            )

        total = query.count()
        query = query.order_by(Bag.is_featured.desc(), Bag.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        items = query.all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    @staticmethod
    def update_bag(db: Session, bag_id: str, data: dict) -> Bag:
        """Update a bag listing (partial update)."""
        bag = db.query(Bag).filter(Bag.id == bag_id).first()
        if not bag:
            raise HTTPException(status_code=404, detail="Bag not found")

        for key, value in data.items():
            if value is not None:
                setattr(bag, key, value)
        db.commit()
        db.refresh(bag)
        return bag

    @staticmethod
    def delete_bag(db: Session, bag_id: str) -> None:
        """Soft-delete a bag by marking it inactive."""
        bag = db.query(Bag).filter(Bag.id == bag_id).first()
        if not bag:
            raise HTTPException(status_code=404, detail="Bag not found")
        bag.is_active = False
        bag.is_available = False
        db.commit()

    @staticmethod
    def add_image(db: Session, bag_id: str, data: dict) -> BagImage:
        """Add an image to a bag."""
        bag = db.query(Bag).filter(Bag.id == bag_id).first()
        if not bag:
            raise HTTPException(status_code=404, detail="Bag not found")

        # If this is the first image or marked as primary, unset other primaries
        if data.get("is_primary"):
            db.query(BagImage).filter(
                BagImage.bag_id == bag_id,
                BagImage.is_primary == True
            ).update({"is_primary": False})

        image = BagImage(bag_id=bag_id, **data)
        db.add(image)
        db.commit()
        db.refresh(image)
        return image

    @staticmethod
    def delete_image(db: Session, image_id: str) -> None:
        """Delete a bag image."""
        image = db.query(BagImage).filter(BagImage.id == image_id).first()
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        db.delete(image)
        db.commit()

    @staticmethod
    def get_brands(db: Session) -> List[str]:
        """Get distinct brands in inventory."""
        results = db.query(Bag.brand).filter(Bag.is_active == True).distinct().all()
        return [r[0] for r in results]

    @staticmethod
    def get_categories(db: Session) -> List[str]:
        """Get distinct categories in inventory."""
        results = db.query(Bag.category).filter(Bag.is_active == True).distinct().all()
        return [r[0] for r in results]