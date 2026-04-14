from .init_db import SessionLocal
from .models import Shop, Product
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
import pandas as pd
from sqlalchemy.orm import Session
from .init_db import engine

def add_shop(title, url):
    session = SessionLocal()

    shop = Shop(title=title, url=url)
    session.add(shop)

    session.commit()
    session.close()


def get_shops():
    session = SessionLocal()

    shops = session.query(Shop).all()

    session.close()
    return shops


def add_product(shop_id, sku, name, price, url):
    session = SessionLocal()

    product = Product(
        shop_id=shop_id,
        sku=sku,
        name=name,
        price=price,
        url=url
    )
    try:
        session.add(product)
        session.commit()
        print(f'Product added: {product.sku} {product.name}')
        return product
    except IntegrityError:
        session.rollback()
        print(f'Already exists: {sku} {name}')
        existing_product = session.query(Product).filter_by(sku=sku).first()
        if existing_product:
            existing_product.price = price
            session.commit()
            print(f'Updated price: {sku} → {price}')
    finally:
        session.close()
        return product
        


def get_products(shop_id):
    session = SessionLocal()
    products = session.query(Product).filter(Product.shop_id == shop_id).all()
    session.close()
    return products



def save_prods_to_excel():
    session = SessionLocal()
    products = (
        session.query(Product)
        .options(joinedload(Product.shop))
        .all()
    )
    data = []
    for p in products:
        data.append({
            "sku": p.sku,
            "name": p.name,
            "price": p.price,
            "url": p.url,
            "shop": p.shop.title
        })

    session.close()
    df = pd.DataFrame(data)
    df.to_excel("products.xlsx", index=False)

    print("Файл products.xlsx создан")