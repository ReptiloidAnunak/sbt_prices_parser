import pandas as pd
import re
import pandas as pd
import re
from supplier.files_parsing.base import BaseParser


class ImiParser(BaseParser):
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

    # =========================
    # CONDUCTORES ELECTRICOS
    # =========================
    def _parse_conductores(self, df):
        result = []

        for i, row in df.iterrows():
            row_values = [str(x).strip() for x in row if pd.notna(x)]

            if len(row_values) < 3:
                continue

            # ищем строку с USD (шапка)
            if "usd" in " ".join(row_values).lower():
                continue

            # пример:
            # [TIPO, MODELO, ..., цена]
            code = row_values[0]
            modelo = row_values[1]

            price = self._extract_price(row_values)

            if price is None:
                continue

            title = f"Conductor electrico {modelo}"

            result.append({
                "code": code,
                "title": title,
                "price": price
            })

        return result

    # =========================
    # BRONCE REFRIGERACION
    # =========================
    def _parse_bronce(self, df):
        result = []

        for _, row in df.iterrows():
            row_values = [str(x).strip() for x in row if pd.notna(x)]

            if len(row_values) < 3:
                continue

            code = row_values[1]  # TIPO
            raw_name = row_values[2]

            price = self._extract_price(row_values)

            if price is None:
                continue

            # Niple M/8mm -> Niple bronce M/8mm
            title = self._insert_bronce(raw_name)

            result.append({
                "code": code,
                "title": title,
                "price": price
            })

        return result

    def _insert_bronce(self, name):
        parts = name.split(" ", 1)
        if len(parts) == 2:
            return f"{parts[0]} bronce {parts[1]}"
        return name

    # =========================
    # FABRICACIONES METALICAS
    # =========================
    def _parse_metalicas(self, df):
        result = []

        for _, row in df.iterrows():
            row_values = [str(x).strip() for x in row if pd.notna(x)]

            if len(row_values) < 2:
                continue

            title = row_values[0]
            price = self._extract_price(row_values)

            if price is None:
                continue

            result.append({
                "code": None,
                "title": title,
                "price": price
            })

        return result

    # =========================
    # ОБЩЕЕ
    # =========================
    def _extract_price(self, row_values):
        for val in reversed(row_values):
            val = str(val).replace(",", ".")
            if re.search(r"\d", val):
                try:
                    return float(re.sub(r"[^\d.]", "", val))
                except:
                    continue
        return None