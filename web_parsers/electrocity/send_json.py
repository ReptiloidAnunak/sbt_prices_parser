


import requests
import json


API_URL = "http://localhost:8010/api/products/import/"


def send_products_json(file_path, supplier):
    products = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                products.append(json.loads(line))
    payload = {
        "supplier": supplier,
        "products": products
    }

    response = requests.post(API_URL, json=payload)

    print("Status:", response.status_code)
    print("Response:", response.text)

    return response


send_products_json('electrocity_products.json', 'Electrocity')