import pandas as pd
from decimal import Decimal, InvalidOperation
from supplier.files_parsing.base import BaseParser


class FavaleParser(BaseParser):
    def __init__(self, supplier=None):
        self.supplier = supplier

    def parse(self, file_path):
        df = pd.read_excel(file_path)
        df.columns = [str(col).strip().upper() for col in df.columns]

        result = []

        for _, row in df.iterrows():
            code = self._clean_value(row.get("CODIGO SKU"))
            title = self._clean_value(row.get("DESCRIPCION"))
            brand = self._clean_value(row.get("MARCA"))
            price = self._clean_decimal(row.get("VALOR"))

            if not code and not title:
                continue

            full_title = f"{title or ''} {brand or ''}".strip()

            result.append({
                "code": str(code).strip() if code else None,
                "title": full_title,
                "brand": brand,
                "price": price,
                "currency": self._get_currency(),
            })

        return result

    def _clean_value(self, value):
        if pd.isna(value):
            return None

        value = str(value).strip()
        if not value or value.lower() in {"nan", "none", "null"}:
            return None

        return value

    def _clean_decimal(self, value):
        if pd.isna(value):
            return None

        value = str(value).strip()
        if not value or value.lower() in {"nan", "none", "null"}:
            return None

        value = value.replace("$", "").replace("p.", "").replace(".", "").replace(",", ".").strip()

        try:
            return Decimal(value)
        except (InvalidOperation, ValueError):
            return None

    def _get_currency(self):
        if self.supplier and getattr(self.supplier, "currency", None):
            return self.supplier.currency
        return "ARS"