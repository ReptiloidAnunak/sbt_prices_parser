import os
import json
import requests

from settings import JSON_FILE, SUPPLIER_NAME


API_URL = os.getenv(
    "API_URL",
    "http://127.0.0.1:8010/api/products/import/"
)


def load_products(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        return []

    # 1. Пробуем как обычный JSON
    try:
        data = json.loads(content)

        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            return [data]

    except json.JSONDecodeError:
        pass

    # 2. Пробуем как JSONL / NDJSON
    products = []
    for i, line in enumerate(content.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue

        try:
            products.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка JSON в строке {i}: {e}")

    return products


def send_products_json(file_path, supplier):
    print("FILE:", file_path)
    print("EXISTS:", os.path.exists(file_path))
    print("SUPPLIER:", supplier)
    print("API_URL:", API_URL)

    products = load_products(file_path)

    print(f"PRODUCTS COUNT: {len(products)}")

    payload = {
        "supplier": supplier,
        "products": products
    }

    try:
        response = requests.post(API_URL, json=payload, timeout=120)

        print(f"STATUS: {response.status_code}")
        print("RESPONSE:")
        print(response.text[:4000])

        return response

    except requests.exceptions.RequestException as e:
        print("REQUEST ERROR:", e)
        return None


if __name__ == "__main__":
    send_products_json(JSON_FILE, SUPPLIER_NAME)