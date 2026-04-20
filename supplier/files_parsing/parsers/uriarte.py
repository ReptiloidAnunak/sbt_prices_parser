import pandas as pd
from supplier.files_parsing.base import BaseParser


class UriarteParser(BaseParser):

    def parse(self, file_path='uriarte.xlsx'):
        all_sheets = pd.read_excel(file_path, sheet_name=None)
        result = []

        for sheet_name, df in all_sheets.items():
            df.columns = df.columns.str.strip()
            target_cols = ['CODIGO UT', 'DESCRIPCION', 'USD LISTA SEPTIEMBRE']

            # Проверяем, есть ли все необходимые колонки
            if not set(target_cols).issubset(df.columns):
                continue

            df_selected = df[target_cols].dropna(subset=['CODIGO UT'])

            for _, row in df_selected.iterrows():
                code = row['CODIGO UT']
                title = row['DESCRIPCION']
                price = row['USD LISTA SEPTIEMBRE']

                result.append({
                    'code': code,
                    'title': title,
                    'price': price,
                    'currency': 'USD',
                    'sheet': sheet_name
                })

        return result