from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from .init_db import Base, engine


class Shop(Base):
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)

    products = relationship("Product", back_populates="shop", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    sku = Column(String, unique=True)
    name = Column(String)
    price = Column(Float)
    url = Column(String, unique=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    shop = relationship("Shop", back_populates="products")


def init_db():
    Base.metadata.create_all(bind=engine)

init_db()