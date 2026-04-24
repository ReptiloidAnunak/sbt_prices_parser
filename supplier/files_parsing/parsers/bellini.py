import pandas as pd
from decimal import Decimal, InvalidOperation
from supplier.files_parsing.base import BaseParser


class BelliniParser(BaseParser):
    def __init__(self, supplier=None):
        self.supplier = supplier

    def parse(self, file_path):
        print("\n\nBelliniParser\n\n")

        df_raw = pd.read_excel(file_path, header=None)

        header_row = self._find_header_row(df_raw)
        df = pd.read_excel(file_path, header=header_row)

        df.columns = df.columns.astype(str).str.strip()

        col_code = "Cód. Artículo"
        col_desc = "Descripción"
        col_price = "PESOS + IVA"

        df = df[[col_code, col_desc, col_price]]
        df = df.dropna(subset=[col_code, col_desc])

        result = []

        for _, row in df.iterrows():
            code = self._clean_value(row.get(col_code))
            desc = self._clean_value(row.get(col_desc))
            price = self._clean_decimal(row.get(col_price))

            if not desc or desc == "...":
                continue

            result.append({
                "code": str(code).strip() if code else None,
                "title": str(desc).strip() if desc else "",
                "price": price,
                "currency": self._get_currency(),
            })

        return result

    def _find_header_row(self, df):
        for i, row in df.iterrows():
            row_str = row.astype(str)
            if row_str.str.contains("Cód. Artículo", case=False).any():
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

        value = value.replace(".", "").replace(",", ".").replace("$", "").strip()

        try:
            return Decimal(value)
        except (InvalidOperation, ValueError):
            return None

    def _get_currency(self):
        if self.supplier and getattr(self.supplier, "currency", None):
            return self.supplier.currency
        return "ARS"