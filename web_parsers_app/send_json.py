import json
import os
import requests


API_URL = os.getenv(
    "API_URL",
    "http://sbt_pars_server:8000/api/products/import/",
)
API_HOST_HEADER = os.getenv("API_HOST_HEADER")
REQUEST_TIMEOUT = int(os.getenv("API_REQUEST_TIMEOUT", "180"))


VALID_PRICE_TYPES = {"wholesale", "retail"}


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


def detect_price_type(parser_name=None, price_type=None):
    """
    По умолчанию все старые парсеры считаются wholesale.
    Если имя парсера заканчивается на _retail, цена уходит в price_retail.
    Можно явно передать price_type="retail" или "wholesale".
    """
    if price_type:
        price_type = str(price_type).lower().strip()
        if price_type not in VALID_PRICE_TYPES:
            raise ValueError(
                f"Invalid price_type: {price_type}. "
                f"Allowed: {', '.join(sorted(VALID_PRICE_TYPES))}"
            )
        return price_type

    parser_name = str(parser_name or "").lower().strip()

    if parser_name.endswith("_retail"):
        return "retail"

    return "wholesale"


def send_products_json(file_path, supplier, parser_name=None, price_type=None):
    products = load_products(file_path)
    detected_price_type = detect_price_type(
        parser_name=parser_name,
        price_type=price_type,
    )

    payload = {
        "supplier": supplier,
        "parser_name": parser_name or "",
        "price_type": detected_price_type,
        "products": products,
    }

    headers = {}
    if API_HOST_HEADER:
        headers["Host"] = API_HOST_HEADER

    response = requests.post(
        API_URL,
        json=payload,
        headers=headers,
        timeout=REQUEST_TIMEOUT,
    )

    if response.status_code >= 400:
        raise requests.HTTPError(
            f"{response.status_code} error from API\n"
            f"URL: {API_URL}\n"
            f"Supplier: {supplier}\n"
            f"Parser name: {parser_name}\n"
            f"Price type: {detected_price_type}\n"
            f"Products count: {len(products)}\n"
            f"First product: {products[0] if products else None}\n"
            f"Response: {response.text[:1000]}",
            response=response,
        )

    try:
        return response.json()
    except ValueError:
        return {"status": "ok", "response_text": response.text}