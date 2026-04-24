import pandas as pd
from decimal import Decimal, InvalidOperation
from supplier.files_parsing.base import BaseParser


class UriarteParser(BaseParser):
    def __init__(self, supplier=None):
        self.supplier = supplier

    def parse(self, file_path="uriarte.xlsx"):
        all_sheets = pd.read_excel(file_path, sheet_name=None)
        result = []

        for sheet_name, df in all_sheets.items():
            df.columns = [str(col).strip() for col in df.columns]
            target_cols = ["CODIGO UT", "DESCRIPCION", "USD LISTA SEPTIEMBRE"]

            if not set(target_cols).issubset(df.columns):
                continue

            df_selected = df[target_cols].dropna(subset=["CODIGO UT"])

            for _, row in df_selected.iterrows():
                code = self._clean_value(row.get("CODIGO UT"))
                title = self._clean_value(row.get("DESCRIPCION"))
                price = self._clean_decimal(row.get("USD LISTA SEPTIEMBRE"))

                if not code:
                    continue

                result.append({
                    "code": str(code).strip(),
                    "title": str(title).strip() if title else "",
                    "price": price,
                    "currency": self._get_currency(),
                    "sheet": sheet_name,
                })

        return result

    def _get_currency(self):
        if self.supplier and getattr(self.supplier, "currency", None):
            return self.supplier.currency
        return "USD"

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
        if not value or value.lower() == "nan":
            return None

        value = value.replace("$", "").replace(",", ".").strip()

        try:
            return Decimal(value)
        except (InvalidOperation, ValueError):
            return None