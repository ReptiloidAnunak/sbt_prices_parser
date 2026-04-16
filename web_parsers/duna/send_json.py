


import requests
import json
import os
from logger import get_logger

logger = get_logger()

API_URL = os.getenv(
    "API_URL",
    "http://host.docker.internal:8010/api/products/import/"
)

def send_products_json(file_path, supplier):
    with open(file_path, 'r', encoding='utf-8') as f:
        products = json.load(f)

    payload = {
        "supplier": supplier,
        "products": products
    }

    response = requests.post(API_URL, json=payload)

    logger.info("Status:", response.status_code)
    logger.info("Response:", response.text)

    return response
