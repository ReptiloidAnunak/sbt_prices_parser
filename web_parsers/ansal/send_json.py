


import requests
import json
from logger import get_logger
import os

API_URL = os.getenv(
    "API_URL",
    "http://host.docker.internal:8010/api/products/import/"
)

logger = get_logger()

def send_products_json(file_path, supplier):
    logger.info("Sending json to server")
    with open(file_path, 'r', encoding='utf-8') as f:
        products = json.load(f)

    payload = {
        "supplier": supplier,
        "products": products
    }

    response = requests.post(API_URL, json=payload)
    logger.info(f"Status: {response.status_code}")
    logger.info(f"Response: {response.text}",)
    return response



if __name__ == "__main__":
    send_products_json()