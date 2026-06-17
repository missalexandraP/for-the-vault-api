"""Inventory catalog endpoints — browse, search, and filter bags."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.inventory import (
    BagCreate, BagUpdate, BagResponse, BagListResponse,
    BagImageCreate, BagImageSchema, BagInventoryFilter,
)
from app.services.inventory_service import InventoryService
from app.utils.security import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/brands", response_model=list[str])
def get_brands(db: Session = Depends(get_db)):
    """Get all available brands."""
    return InventoryService.get_brands(db)


@router.get("/categories", response_model=list[str])
def get_categories(db: Session = Depends(get_db)):
    """Get all available categories."""
    return InventoryService.get_categories(db)


@router.get("", response_model=BagListResponse)
def list_bags(
    brand: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    is_available: Optional[bool] = Query(None),
    is_featured: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db_session: Session = Depends(get_db),
):
    """List available bags with filtering and search."""
    return InventoryService.list_bags(
        db=db_session,
        brand=brand,
        category=category,
        min_price=min_price,
        max_price=max_price,
        is_available=is_available,
        is_featured=is_featured,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get("/{bag_id}", response_model=BagResponse)
def get_bag(bag_id: str, db: Session = Depends(get_db)):
    """Get details for a specific bag."""
    return InventoryService.get_bag(db=db, bag_id=bag_id)


# --- Admin-only inventory management ---

@router.post("", response_model=BagResponse, status_code=201)
def create_bag(
    data: BagCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: create a new bag listing."""
    return InventoryService.create_bag(db=db, data=data.model_dump())


@router.put("/{bag_id}", response_model=BagResponse)
def update_bag(
    bag_id: str,
    data: BagUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: update a bag listing."""
    return InventoryService.update_bag(db=db, bag_id=bag_id, data=data.model_dump(exclude_none=True))


@router.delete("/{bag_id}", status_code=204)
def delete_bag(
    bag_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: soft-delete a bag listing."""
    InventoryService.delete_bag(db=db, bag_id=bag_id)


@router.post("/{bag_id}/images", response_model=BagImageSchema, status_code=201)
def add_image(
    bag_id: str,
    data: BagImageCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: add an image to a bag listing."""
    return InventoryService.add_image(db=db, bag_id=bag_id, data=data.model_dump())


@router.delete("/{bag_id}/images/{image_id}", status_code=204)
def delete_image(
    bag_id: str,
    image_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin: delete an image from a bag listing."""
    InventoryService.delete_image(db=db, image_id=image_id)