import requests
from bs4 import BeautifulSoup
import time
import random
from utils import get_prods_from_page, save_to_json, get_useragents
from settings import DATA_FOLDER
import os
import json

USER_AGENTS = get_useragents()

def sleep_random(a=2, b=5):
    time.sleep(random.uniform(a, b))

class ShopML():
    def __init__(self, title, url):
        self.title = title
        self.url = url
        self.products = []
        self.json = DATA_FOLDER / self._set_json_path()

        if not os.path.exists(self.json):
            with open(self.json, 'w') as f:
                f.write(json.dumps([]))

    def _set_json_path(self):
        return f"{self.title.lower()}.json"



def parse_ml_shop(shop: ShopML):
    session = requests.Session()
    prods_by_page = 0
    while prods_by_page < 100:
        prods_by_page += 48
        pag_segment = f"_Desde_{prods_by_page}_NoIndex_True"
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

            save_to_json(shop, prods_dicts_lst)

            sleep_random(3, 7)

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] {e}")
            sleep_random(5, 10)


shop = ShopML(title="Masqueprecios",
              url="https://listado.mercadolibre.com.ar/tienda/masqueprecios/"
              )

print(shop.json)

parse_ml_shop(shop)