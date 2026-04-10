from .init_db import SessionLocal
from .models import Shop, Product
from sqlalchemy.exc import IntegrityError

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
        session.close()
        return product
    except IntegrityError:
        print(f'Already exists: {sku} {name}')
        session.rollback()
        session.close()
        return
        


def get_products(shop_id):
    session = SessionLocal()

    products = session.query(Product).filter(Product.shop_id == shop_id).all()

    session.close()
    return products