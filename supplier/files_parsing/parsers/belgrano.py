import pandas as pd
from supplier.files_parsing.base import BaseParser


class BelgranoParser(BaseParser):

    def parse(self, file_path):
        df_raw = pd.read_excel(file_path, header=None)

        header_row = self._find_header_row(df_raw)
        df = pd.read_excel(file_path, header=header_row)

        df.columns = df.columns.str.strip().str.lower()

        col_codigo = self._find_column(df, "cod")
        idx = df.columns.get_loc(col_codigo)

        col_producto = df.columns[idx + 1]
        col_precio = self._find_price_column(df)
        col_moneda = self._find_currency_column(df)

        result = self._build_result(
            df,
            col_codigo,
            col_producto,
            col_precio,
            col_moneda
        )

        return result

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

        if col_moneda:
            result = df[[col_codigo, col_producto, col_moneda, col_precio]].copy()
            result.columns = ["code", "title", "currency", "price"]
        else:
            result = df[[col_codigo, col_producto, col_precio]].copy()
            result.columns = ["code", "title", "price"]
            result["currency"] = "ARS"

        result = result[result["title"] != result["code"]]
        result = result.dropna()

        return result.to_dict(orient="records")