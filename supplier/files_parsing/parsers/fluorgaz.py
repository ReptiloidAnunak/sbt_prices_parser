import pandas as pd
from supplier.files_parsing.base import BaseParser


class FluorgazParser(BaseParser):

    def parse(self, file_path):
        df_raw = pd.read_excel(file_path, header=None)

        header_row = self._find_header_row(df_raw)
        df = pd.read_excel(file_path, header=header_row)

        df.columns = df.columns.astype(str).str.strip()

        col_product = "PRODUCTO"
        col_price = "PRECIO USD X UNIDAD"

        df = df[[col_product, col_price]]

        df = df.dropna(subset=[col_product, col_price])

        df[col_price] = self._clean_price(df[col_price])

        result = self._build_result(df, col_product, col_price)

        return result

    def _find_header_row(self, df):
        for i, row in df.iterrows():
            row_str = row.astype(str)
            if row_str.str.contains("PRODUCTO", case=False).any():
                return i
        raise ValueError("Не найдена строка заголовков")

    def _clean_price(self, series):
        return (
            series
            .astype(str)
            .str.replace(',', '.', regex=False)
            .pipe(pd.to_numeric, errors='coerce')
        )

    def _build_result(self, df, col_product, col_price):
        result = []

        for _, row in df.iterrows():
            product = str(row[col_product]).strip()
            price = row[col_price]

            if not product or product == '...':
                continue

            result.append({
                "code": None,  # ⚠️ нет кода — оставляем None
                "title": product,
                "price": price,
                "currency": "USD",
            })

        return result