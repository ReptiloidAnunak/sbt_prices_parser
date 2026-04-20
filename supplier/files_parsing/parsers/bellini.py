import pandas as pd
from supplier.files_parsing.base import BaseParser


class BelliniParser(BaseParser):

    def parse(self, file_path):
        print('\n\nBelliniParser\n\n')
        df_raw = pd.read_excel(file_path, header=None)

        header_row = self._find_header_row(df_raw)
        df = pd.read_excel(file_path, header=header_row)

        df.columns = df.columns.astype(str).str.strip()

        col_code = "Cód. Artículo"
        col_desc = "Descripción"
        col_price = "PESOS + IVA"

        df = df[[col_code, col_desc, col_price]]

        df = df.dropna(subset=[col_code, col_desc])

        df[col_price] = self._clean_price(df[col_price])

        result = self._build_result(df, col_code, col_desc, col_price)

        return result

    def _find_header_row(self, df):
        for i, row in df.iterrows():
            row_str = row.astype(str)
            if row_str.str.contains('Cód. Artículo', case=False).any():
                return i
        raise ValueError("Не найдена строка заголовков")

    def _clean_price(self, series):
        return (
            series
            .astype(str)
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .pipe(pd.to_numeric, errors='coerce')
        )

    def _build_result(self, df, col_code, col_desc, col_price):
        result = []

        for _, row in df.iterrows():
            code = str(row[col_code]).strip()
            desc = str(row[col_desc]).strip()
            price = row[col_price]

            if not desc or desc == '...':
                continue

            result.append({
                "code": code,
                "title": desc,
                "price": price,
                "currency": "ARS",
            })

        return result