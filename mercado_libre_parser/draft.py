import requests

item_id = "MLA123456789"

res = requests.get(
    f"https://api.mercadolibre.com/items/{item_id}",
    headers={"User-Agent": "Mozilla/5.0"}
)

print(res.json())