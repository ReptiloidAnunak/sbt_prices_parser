import pandas as pd
from decimal import Decimal, InvalidOperation
from supplier.files_parsing.base import BaseParser


class CasaJarseParser(BaseParser):
    def __init__(self, supplier=None):
        self.supplier = supplier

    def parse(self, file_path="casa_jarse.xlsx"):
        df = pd.read_excel(file_path, skiprows=3)
        df.columns = [str(col).strip() for col in df.columns]

        col_code = self._find_column(df, ["codigo", "cуdigo"])
        col_desc = self._find_column(df, ["descripcion", "descripci"])
        col_price = self._find_column(df, ["precio"])

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

    def _find_column(self, df, keywords):
        for keyword in keywords:
            matches = [c for c in df.columns if keyword.lower() in str(c).lower()]
            if matches:
                return matches[0]

        raise ValueError(f"Колонка с ключами {keywords} не найдена")

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

        value = value.replace("$", "").replace(".", "").replace(",", ".").strip()

        try:
            return Decimal(value)
        except (InvalidOperation, ValueError):
            return None

    def _get_currency(self):
        if self.supplier and getattr(self.supplier, "currency", None):
            return self.supplier.currency
        return "ARS"