import os
import re
import pandas as pd
from decimal import Decimal, InvalidOperation
from supplier.files_parsing.base import BaseParser


class NuevaHeraParser(BaseParser):
    def __init__(self, supplier=None):
        self.supplier = supplier

    def parse_file(self, file_path):
        if not os.path.exists(file_path):
            print(f"Файл {file_path} не найден")
            return []

        try:
            print(f"\n=== Обработка файла: {file_path} ===")
            return self.parse(file_path)
        except Exception as e:
            print(f"Ошибка в {file_path}: {e}")
            return []

    def parse_folder(self, folder_path="price_lists"):
        if not os.path.exists(folder_path):
            print(f"Папка {folder_path} не найдена")
            return []

        files = [
            os.path.join(folder_path, f)
            for f in os.listdir(folder_path)
            if f.endswith(".xlsx")
        ]

        all_results = []

        for file_path in files:
            try:
                print(f"\n=== Обработка файла: {file_path} ===")
                results = self.parse(file_path)
                all_results.extend(results)
            except Exception as e:
                print(f"Ошибка в {file_path}: {e}")

        return all_results

    def parse(self, file_path):
        df_raw = pd.read_excel(file_path, header=None)
        result = []

        for _, row in df_raw.iterrows():
            row_values = [str(val).strip() if pd.notna(val) else "" for val in row]

            if not any(row_values):
                continue

            code_idx = self._find_code_index(row_values)
            if code_idx == -1:
                continue

            price_idx = self._find_price_index(row_values, code_idx)
            if price_idx == -1 or price_idx <= code_idx:
                continue

            code = self._clean_value(row_values[code_idx])
            title = " ".join(
                [row_values[i] for i in range(code_idx + 1, price_idx) if row_values[i]]
            ).strip()
            price = self._clean_price(row_values[price_idx])

            if code or title:
                result.append({
                    "code": str(code).strip() if code else None,
                    "title": title,
                    "price": price,
                    "currency": self._get_currency(default="USD"),
                })

        return result

    def _find_code_index(self, row_values):
        for i in [0, 1]:
            if i < len(row_values):
                val = row_values[i].lower()
                if "cod" in val or (val and val.isdigit()):
                    return i
        return -1

    def _find_price_index(self, row_values, code_idx):
        for i in range(len(row_values) - 1, code_idx, -1):
            val = row_values[i].lower()
            if "u$s" in val or (val and any(c.isdigit() for c in val)):
                return i
        return -1

    def _clean_price(self, raw_price):
        if raw_price is None:
            return None

        raw_price = str(raw_price).strip()
        if not raw_price or raw_price.lower() in {"nan", "none", "null"}:
            return None

        clean = re.sub(r"[^\d,.]", "", raw_price).replace(",", ".").strip()

        try:
            return Decimal(clean) if clean else None
        except (InvalidOperation, ValueError):
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