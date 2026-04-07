
import pandas as pd
from supplier.files_parsing.base import BaseParser


class CasaJarseParser(BaseParser):

    def parse(self, file_path='casa_jarse.xlsx'):
        df = pd.read_excel(file_path, skiprows=3)
        df.columns = df.columns.str.strip()
        col_code = self._find_column(df, ['codigo', 'cуdigo'])
        col_desc = self._find_column(df, ['descripcion', 'descripci'])
        col_price = self._find_column(df, ['precio'])

        result = []

        for _, row in df.iterrows():
            code = row.get(col_code)
            title = row.get(col_desc)
            price = row.get(col_price)

            if pd.notna(code) or pd.notna(title):
                result.append({
                    'code': str(code).strip() if pd.notna(code) else None,
                    'title': str(title).strip() if pd.notna(title) else None,
                    'price': float(price) if pd.notna(price) else None
                })

        return result

    def _find_column(self, df, keywords):
        for keyword in keywords:
            matches = [c for c in df.columns if keyword.lower() in str(c).lower()]
            if matches:
                return matches[0]

        raise ValueError(f"Колонка с ключами {keywords} не найдена")