import re
import pandas as pd
from decimal import Decimal, InvalidOperation
from supplier.files_parsing.base import BaseParser


class ImiParser(BaseParser):
    def __init__(self, supplier=None):
        self.supplier = supplier

    def parse(self, file_path):
        df = pd.read_excel(file_path, header=None)

        text = " ".join(df.astype(str).fillna("").values.flatten()).lower()

        if "conductores electricos" in text:
            return self._parse_conductores(df)
        elif "bronce refrigeracion" in text:
            return self._parse_bronce(df)
        elif "fabricaciones metalicas" in text:
            return self._parse_metalicas(df)
        else:
            raise ValueError("Неизвестный формат файла")

    def _parse_conductores(self, df):
        result = []

        for _, row in df.iterrows():
            row_values = [str(x).strip() for x in row if pd.notna(x)]

            if len(row_values) < 3:
                continue

            if "usd" in " ".join(row_values).lower():
                continue

            code = self._clean_value(row_values[0])
            modelo = self._clean_value(row_values[1])
            price = self._extract_price(row_values)

            if price is None:
                continue

            title = f"Conductor electrico {modelo}" if modelo else "Conductor electrico"

            result.append({
                "code": str(code).strip() if code else None,
                "title": title,
                "price": price,
                "currency": self._get_currency(default="USD"),
            })

        return result

    def _parse_bronce(self, df):
        result = []

        for _, row in df.iterrows():
            row_values = [str(x).strip() for x in row if pd.notna(x)]

            if len(row_values) < 3:
                continue

            code = self._clean_value(row_values[1])
            raw_name = self._clean_value(row_values[2])
            price = self._extract_price(row_values)

            if price is None:
                continue

            title = self._insert_bronce(raw_name) if raw_name else ""

            result.append({
                "code": str(code).strip() if code else None,
                "title": title,
                "price": price,
                "currency": self._get_currency(default="USD"),
            })

        return result

    def _parse_metalicas(self, df):
        result = []

        for _, row in df.iterrows():
            row_values = [str(x).strip() for x in row if pd.notna(x)]

            if len(row_values) < 2:
                continue

            title = self._clean_value(row_values[0])
            price = self._extract_price(row_values)

            if price is None:
                continue

            result.append({
                "code": None,
                "title": str(title).strip() if title else "",
                "price": price,
                "currency": self._get_currency(default="USD"),
            })

        return result

    def _insert_bronce(self, name):
        parts = name.split(" ", 1)
        if len(parts) == 2:
            return f"{parts[0]} bronce {parts[1]}"
        return name

    def _extract_price(self, row_values):
        for val in reversed(row_values):
            val = str(val).strip().replace(",", ".")
            if re.search(r"\d", val):
                cleaned = re.sub(r"[^\d.]", "", val)
                try:
                    return Decimal(cleaned) if cleaned else None
                except (InvalidOperation, ValueError):
                    continue
        return None

    def _clean_value(self, value):
        if value is None:
            return None

        value = str(value).strip()
        if not value or value.lower() in {"nan", "none", "null"}:
            return None

        return value

    def _get_currency(self, default="ARS"):
        if self.supplier and getattr(self.supplier, "currency", None):
            return self.supplier.currency
        return default