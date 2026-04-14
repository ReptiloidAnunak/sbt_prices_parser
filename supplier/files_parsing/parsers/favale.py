import pandas as pd
import os
from supplier.files_parsing.base import BaseParser


class FavaleParser(BaseParser):

    def parse(self, file_path):
        df = pd.read_excel(file_path)  # <-- просто так, без header=None

        df.columns = [str(col).strip().upper() for col in df.columns]

        result = []

        for _, row in df.iterrows():
            code = str(row.get("CODIGO SKU", "")).strip()
            title = str(row.get("DESCRIPCION", "")).strip()
            brand = str(row.get("MARCA", "")).strip()
            price = self._clean_price(row.get("VALOR"))

            if not code and not title:
                continue

            result.append({
                "code": code,
                "title": f"{title} {brand}".strip(),
                "brand": brand,
                "price": price
            })

        return result

    def _clean_price(self, price):
        if price is None:
            return 0

        if isinstance(price, (int, float)):
            return float(price)

        price = str(price).strip()
        price = price.replace('$', '').replace(',', '.').replace('p.', '')

        try:
            return float(price)
        except ValueError:
            return 0