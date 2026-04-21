import requests
import json
import os

from settings import JSON_FILE, SUPPLIER_NAME


API_URL = os.getenv(
    "API_URL",
    "http://127.0.0.1:8010/api/products/import/"
)


def send_products_json(file_path, supplier):
    print("📂 FILE:", file_path)
    print("📂 EXISTS:", os.path.exists(file_path))

    if not os.path.exists(file_path):
        print("❌ Файл не найден")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        products = json.load(f)

    print(f"📦 Products count: {len(products)}")

    payload = {
        "supplier": supplier,
        "products": products
    }

    try:
        response = requests.post(API_URL, json=payload, timeout=30)

        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:1000]}")

        return response

    except requests.exceptions.RequestException as e:
        print("❌ Ошибка запроса:", e)


if __name__ == "__main__":
    send_products_json(JSON_FILE, SUPPLIER_NAME)