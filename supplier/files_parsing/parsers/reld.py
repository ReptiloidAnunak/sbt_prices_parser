import pandas as pd
from decimal import Decimal, InvalidOperation
from supplier.files_parsing.base import BaseParser


class ReldParser(BaseParser):
    def __init__(self, supplier=None):
        self.supplier = supplier

    def parse(self, file_path="reld.xlsx"):
        df = pd.read_excel(file_path, skiprows=4)
        df.columns = [str(col).strip() for col in df.columns]

        col_code = self._find_column(df, "Codigo")
        col_desc = self._find_column(df, "Descripcion")
        col_price = self._find_column(df, "Precio S/IVA")

        result = []

        for _, row in df.iterrows():
            code = self._clean_value(row.get(col_code))
            title = self._clean_value(row.get(col_desc))
            price = self._clean_decimal(row.get(col_price))

            if code or title:
                result.append({
                    "code": str(code).strip() if code else None,
                    "title": str(title).strip() if title else "",
                    "price": price,
                    "currency": self._get_currency(),
                })

        return result

    def _find_column(self, df, keyword):
        matches = [c for c in df.columns if keyword.lower() in c.lower()]
        if not matches:
            raise ValueError(f"Колонка с '{keyword}' не найдена")
        return matches[0]

    def _get_currency(self):
        if self.supplier and getattr(self.supplier, "currency", None):
            return self.supplier.currency
        return "ARS"

    def _clean_value(self, value):
        if pd.isna(value):
            return None

        value = str(value).strip()
        if not value or value.lower() == "nan":
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