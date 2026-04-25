import json
import os
import requests


API_URL = os.getenv(
    "API_URL",
    "http://sbt_pars_server:8000/api/products/import/"
)


def load_products(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        return []

    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
        return [data]
    except json.JSONDecodeError:
        products = []
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            products.append(json.loads(line))
        return products


def send_products_json(file_path, supplier):
    products = load_products(file_path)

    payload = {
        "supplier": supplier,
        "products": products,
    }

    response = requests.post(
        API_URL,
        json=payload,
        headers={"Host": "localhost"},
        timeout=120,
    )

    if response.status_code >= 400:
        raise requests.HTTPError(
            f"{response.status_code} error from API\n"
            f"URL: {API_URL}\n"
            f"Supplier: {supplier}\n"
            f"Products count: {len(products)}\n"
            f"First product: {products[0] if products else None}\n"
            f"Response: {response.text[:1000]}",
            response=response,
        )

    try:
        return response.json()
    except ValueError:
        return {"status": "ok", "response_text": response.text}