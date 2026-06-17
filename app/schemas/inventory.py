"""Pydantic schemas for bag inventory."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class BagImageSchema(BaseModel):
    id: str
    url: str
    alt_text: Optional[str] = None
    is_primary: bool
    sort_order: int

    class Config:
        from_attributes = True


class BagCreate(BaseModel):
    brand: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1, max_length=255)
    category: str = "other"
    description: Optional[str] = None
    color: Optional[str] = None
    material: Optional[str] = None
    market_value: float = Field(..., gt=0)
    rental_price_per_day: float = Field(..., gt=0)
    deposit_amount: float = Field(..., ge=0)
    condition: str = "excellent"
    year: Optional[int] = None
    stock_quantity: int = 1
    size_info: Optional[str] = None
    authentication_notes: Optional[str] = None
    is_featured: bool = False


class BagUpdate(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    material: Optional[str] = None
    market_value: Optional[float] = None
    rental_price_per_day: Optional[float] = None
    deposit_amount: Optional[float] = None
    condition: Optional[str] = None
    year: Optional[int] = None
    is_available: Optional[bool] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None
    stock_quantity: Optional[int] = None
    size_info: Optional[str] = None
    authentication_notes: Optional[str] = None


class BagResponse(BaseModel):
    id: str
    brand: str
    model: str
    category: str
    description: Optional[str] = None
    color: Optional[str] = None
    material: Optional[str] = None
    market_value: float
    rental_price_per_day: float
    deposit_amount: float
    condition: str
    year: Optional[int] = None
    is_available: bool
    is_featured: bool
    stock_quantity: int
    size_info: Optional[str] = None
    authentication_notes: Optional[str] = None
    images: List[BagImageSchema] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BagListResponse(BaseModel):
    items: List[BagResponse]
    total: int
    page: int
    page_size: int


class BagImageCreate(BaseModel):
    url: str
    alt_text: Optional[str] = None
    is_primary: bool = False
    sort_order: int = 0


class BagInventoryFilter(BaseModel):
    brand: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    is_available: Optional[bool] = None
    is_featured: Optional[bool] = None
    search: Optional[str] = None