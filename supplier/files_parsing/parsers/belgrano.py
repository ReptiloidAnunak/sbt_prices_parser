import pandas as pd
from decimal import Decimal, InvalidOperation
from supplier.files_parsing.base import BaseParser


class BelgranoParser(BaseParser):
    def __init__(self, supplier=None):
        self.supplier = supplier

    def parse(self, file_path):
        df_raw = pd.read_excel(file_path, header=None)

        header_row = self._find_header_row(df_raw)
        df = pd.read_excel(file_path, header=header_row)

        df.columns = [str(col).strip().lower() for col in df.columns]

        col_codigo = self._find_column(df, "cod")
        idx = df.columns.get_loc(col_codigo)

        if idx + 1 >= len(df.columns):
            raise ValueError("Не найдена колонка с названием товара после кода")

        col_producto = df.columns[idx + 1]
        col_precio = self._find_price_column(df)
        col_moneda = self._find_currency_column(df)

        return self._build_result(
            df,
            col_codigo,
            col_producto,
            col_precio,
            col_moneda
        )

    def _find_header_row(self, df_raw):
        for i, row in df_raw.iterrows():
            row_str = row.astype(str).str.lower()
            if row_str.str.contains("cod").any():
                return i
        raise ValueError("Не найдена строка заголовков")

    def _find_column(self, df, keyword):
        cols = [c for c in df.columns if keyword in c]
        if not cols:
            raise ValueError(f"Колонка с '{keyword}' не найдена")
        return cols[0]

    def _find_price_column(self, df):
        cols = [c for c in df.columns if "precio" in c and "iva" in c]
        if not cols:
            raise ValueError("Колонка с ценой не найдена")
        return cols[0]

    def _find_currency_column(self, df):
        cols = [
            c for c in df.columns
            if any(k in c for k in ["moneda", "usd", "currency", "$"])
        ]
        return cols[0] if cols else None

    def _build_result(self, df, col_codigo, col_producto, col_precio, col_moneda):
        result = []

        for _, row in df.iterrows():
            code = self._clean_value(row.get(col_codigo))
            title = self._clean_value(row.get(col_producto))
            price = self._clean_decimal(row.get(col_precio))

            if not code and not title:
                continue

            if title and code and str(title).strip() == str(code).strip():
                continue

            currency = self._normalize_currency(
                row.get(col_moneda) if col_moneda else None
            )

            result.append({
                "code": str(code).strip() if code else None,
                "title": str(title).strip() if title else "",
                "price": price,
                "currency": currency,
            })

        return result

    def _normalize_currency(self, raw_currency):
        if raw_currency is not None and str(raw_currency).strip():
            value = str(raw_currency).strip().upper()

            if "USD" in value or "U$S" in value:
                return "USD"

            if "ARS" in value or "PESO" in value or "$" == value:
                return "ARS"

        if self.supplier and getattr(self.supplier, "currency", None):
            return self.supplier.currency

        return "ARS"

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