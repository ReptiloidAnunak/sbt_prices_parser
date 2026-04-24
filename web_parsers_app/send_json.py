import json
import os

import requests


API_URL = os.getenv(
    "API_URL",
    "http://sbt_pars_server:8000/api/products/import/"
)


def send_products_json(file_path, supplier):
    with open(file_path, "r", encoding="utf-8") as f:
        products = json.load(f)

    payload = {
        "supplier": supplier,
        "products": products,
    }

    response = requests.post(API_URL, json=payload, timeout=120)

    print("Status:", response.status_code)
    print("Response:", response.text)

    response.raise_for_status()

    return response