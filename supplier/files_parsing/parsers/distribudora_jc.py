import pandas as pd
from supplier.files_parsing.base import BaseParser


class JcParser(BaseParser):

    def parse(self, file_path='Lista-JC.xlsx'):
        # Читаем без заголовков
        df = pd.read_excel(file_path, skiprows=15, header=None)

        # Удаляем полностью пустые строки
        df = df.dropna(how='all')

        # Берем строку с заголовками
        header_row = df.iloc[0]
        df = df[1:]  # убираем строку заголовков

        # Назначаем названия колонок
        df.columns = header_row
        df.columns = df.columns.str.strip()

        # Ищем нужные колонки
        col_code = self._find_column(df, 'CODIGO')
        col_desc = self._find_column(df, 'DESCRIPCION')
        col_price = self._find_column(df, 'PRECIO')

        result = []

        for _, row in df.iterrows():
            code = row[col_code]
            title = row[col_desc]
            price = row[col_price]

            if pd.notna(code) or pd.notna(title):
                result.append({
                    'code': str(code).strip() if pd.notna(code) else None,
                    'title': str(title).strip() if pd.notna(title) else None,
                    'price': float(price) if pd.notna(price) else None
                })

        return result

    def _find_column(self, df, keyword):
        matches = [c for c in df.columns if keyword.lower() in str(c).lower()]
        if not matches:
            raise ValueError(f"Колонка с '{keyword}' не найдена")
        return matches[0]