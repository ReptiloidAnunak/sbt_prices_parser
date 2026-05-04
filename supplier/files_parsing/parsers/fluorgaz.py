import pandas as pd
from decimal import Decimal, InvalidOperation
from supplier.files_parsing.base import BaseParser


import re

def normalize_title(value):
    if not value:
        return None
    value = str(value)
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip().upper()



class FluorgazParser(BaseParser):
    def __init__(self, supplier=None):
        self.supplier = supplier

    def parse(self, file_path):
        df_raw = pd.read_excel(file_path, header=None)

        header_row = self._find_header_row(df_raw)
        df = pd.read_excel(file_path, header=header_row)
        df.columns = df.columns.str.replace('\xa0', ' ', regex=False)
        df.columns = [str(col).strip() for col in df.columns]

        col_product = "PRODUCTO"
        col_price = "PRECIO USD X UNIDAD"

        df = df[[col_product, col_price]]
        df = df.dropna(subset=[col_product, col_price])

        result = []

        for _, row in df.iterrows():
            product = self._clean_value(row.get(col_product))
            price = self._clean_decimal(row.get(col_price))

            if not product or product == "...":
                continue

            result.append({
                "code": None,
                "title": normalize_title(product),
                "price": price,
                "currency": self._get_currency(default="USD"),
            })

        return result

    def _find_header_row(self, df):
        for i, row in df.iterrows():
            row_str = row.astype(str)
            if row_str.str.contains("PRODUCTO", case=False).any():
                return i
        raise ValueError("Не найдена строка заголовков")

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

        value = value.replace("$", "").replace(",", ".").strip()

        try:
            return Decimal(value)
        except (InvalidOperation, ValueError):
            return None

    def _get_currency(self, default="ARS"):
        if self.supplier and getattr(self.supplier, "currency", None):
            return self.supplier.currency
        return default