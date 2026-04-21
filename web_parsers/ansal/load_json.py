


import requests
import json
import os
from logger import get_logger

from settings  import JSON_FILE, SUPPLIER_NAME


API_URL = os.getenv(
    "API_URL",
    "http://127.0.0.1:8010/api/products/import/"
)

def send_products_json(file_path, supplier):
    with open(file_path, 'r', encoding='utf-8') as f:
        products = json.load(f)

    payload = {
        "supplier": supplier,
        "products": products
    }

    response = requests.post(API_URL, json=payload)

    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

    return response


send_products_json(JSON_FILE, SUPPLIER_NAME)