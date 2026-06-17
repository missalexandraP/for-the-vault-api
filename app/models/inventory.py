"""Bag inventory models — the core product catalog."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Float, Boolean, DateTime, ForeignKey, Integer, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.database import Base
import enum


def generate_uuid():
    return str(uuid.uuid4())


class BagCategory(str, enum.Enum):
    TOTE = "tote"
    CROSSBODY = "crossbody"
    SHOULDER = "shoulder"
    CLUTCH = "clutch"
    BACKPACK = "backpack"
    SATCHEL = "satchel"
    HOBO = "hobo"
    BUCKET = "bucket"
    DUFFLE = "duffle"
    OTHER = "other"


class Bag(Base):
    __tablename__ = "bags"

    id = Column(String, primary_key=True, default=generate_uuid)
    brand = Column(String(100), nullable=False, index=True)
    model = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False, default=BagCategory.OTHER)
    description = Column(Text, nullable=True)
    color = Column(String(100), nullable=True)
    material = Column(String(100), nullable=True)
    market_value = Column(Float, nullable=False)  # Current market value in USD
    rental_price_per_day = Column(Float, nullable=False)  # Daily rental price
    deposit_amount = Column(Float, nullable=False)  # Security deposit
    condition = Column(String(50), default="excellent")  # excellent, good, fair
    year = Column(Integer, nullable=True)
    is_available = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    stock_quantity = Column(Integer, default=1)  # How many units of this bag we have
    size_info = Column(String(255), nullable=True)  # Dimensions or size description
    authentication_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    images = relationship("BagImage", back_populates="bag", cascade="all, delete-orphan",
                          order_by="BagImage.sort_order")

    def __repr__(self):
        return f"<Bag {self.brand} {self.model}>"


class BagImage(Base):
    """Images associated with a bag — multiple angles."""
    __tablename__ = "bag_images"

    id = Column(String, primary_key=True, default=generate_uuid)
    bag_id = Column(String, ForeignKey("bags.id"), nullable=False)
    url = Column(Text, nullable=False)
    alt_text = Column(String(255), nullable=True)
    is_primary = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    bag = relationship("Bag", back_populates="images")

    def __repr__(self):
        return f"<BagImage {self.url[:50]}>"