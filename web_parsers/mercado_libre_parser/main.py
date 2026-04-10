import requests
from bs4 import BeautifulSoup
import time
import random
from settings import DATA_FOLDER
from utils  import get_useragents, get_prods_from_page, save_prods_db
import os
import json
from data_base.models import Shop, Product
from data_base.tools import get_shops

USER_AGENTS = get_useragents()

def sleep_random(a=2, b=5):
    time.sleep(random.uniform(a, b))


def normalize_url(url: str):
    if "www.mercadolibre.com.ar/tienda/" in url:
        shop_name = url.split("/tienda/")[1].strip("/")
        return f"https://listado.mercadolibre.com.ar/tienda/{shop_name}/"
    return url


def normalize_url(url: str):
    if "mercadolibre.com.ar/tienda/" in url:
        name = url.split("/tienda/")[1].strip("/")
        return f"https://listado.mercadolibre.com.ar/tienda/{name}/"
    return url


def parse_ml_shop(shop: Shop):
    session = requests.Session()
    prods_by_page = 0
    
    while prods_by_page < 100:
        prods_by_page += 48
        pag_segment = f"_Desde_{prods_by_page}_NoIndex_True"
        shop.url = normalize_url(shop.url)
        pag_link = shop.url + pag_segment

        headers = {
                    "User-Agent": random.choice(USER_AGENTS),
                    "Accept-Language": random.choice([
                        "es-AR,es;q=0.9,en;q=0.8",
                        "en-US,en;q=0.9",
                        "es-ES,es;q=0.9,en;q=0.8"
                    ]),
                    "Accept": "text/html,application/xhtml+xml",
                    "Connection": "keep-alive",
                }
        
        print(f"[INFO] Requesting: {pag_link}")

        try:
            response = session.get(pag_link, headers=headers, timeout=10)

            if response.status_code != 200:
                print(f"[WARN] Status code: {response.status_code}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            prods_dicts_lst = get_prods_from_page(soup)
            # print(prods_dicts_lst)
            save_prods_db(shop, prods_dicts_lst)
            sleep_random(5, 5)

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] {e}")
            sleep_random(5, 10)



def run_app():
    shops = get_shops()
    for shop in shops:
        print(shop.title.capitalize())
        print(shop.url)
        parse_ml_shop(shop)


if __name__ == "__main__":
    run_app()
