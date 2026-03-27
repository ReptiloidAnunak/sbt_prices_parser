from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    event
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)

    # Main data
    category = Column(String(255))
    product_name = Column(String(255))

    # Ansal
    ansal_code = Column(String(50))
    ansal_name = Column(String(255))
    ansal_price_wholesale = Column(Numeric(10, 2))
    ansal_price_retail = Column(Numeric(10, 2))

    # Reld
    reld_code = Column(String(50))
    reld_name = Column(String(255))
    reld_price_wholesale = Column(Numeric(10, 2))
    reld_price_retail = Column(Numeric(10, 2))

    # Best price
    best_supplier = Column(String(50))
    best_price = Column(Numeric(10, 2))

    @hybrid_property
    def best_price_label(self):
        if self.best_supplier and self.best_price:
            return f"{self.best_supplier}: {self.best_price}"
        return None


# --- Логика вычисления лучшей цены ---

def set_best_price(mapper, connection, target: Product):
    prices = {
        "ansal": target.ansal_price_wholesale,
        "reld": target.reld_price_wholesale,
    }

    # убираем None
    prices = {k: v for k, v in prices.items() if v is not None}

    if prices:
        supplier, price = min(prices.items(), key=lambda x: x[1])
        target.best_supplier = supplier
        target.best_price = price
    else:
        target.best_supplier = None
        target.best_price = None


# --- Авто-вызов перед insert/update ---
event.listen(Product, "before_insert", set_best_price)
event.listen(Product, "before_update", set_best_price)