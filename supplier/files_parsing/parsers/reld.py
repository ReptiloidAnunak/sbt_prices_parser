import pandas as pd
from supplier.files_parsing.base import BaseParser


class ReldParser(BaseParser):

    def parse(self, file_path='reld.xlsx'):
        df = pd.read_excel(file_path, skiprows=4)
        df.columns = df.columns.str.strip()  # Очистка названий колонок

        col_code = self._find_column(df, 'Codigo')
        col_desc = self._find_column(df, 'Descripcion')
        col_price = self._find_column(df, 'Precio S/IVA')
        result = []
        for _, row in df.iterrows():
            code = row[col_code]
            title = row[col_desc]
            price = row[col_price]

            if pd.notna(code) or pd.notna(title):
                result.append({
                    'code': code,
                    'title': title,
                    'price': price
                })

        return result

    def _find_column(self, df, keyword):
        # Поиск колонки по ключевому слову (регистронезависимо)
        matches = [c for c in df.columns if keyword.lower() in c.lower()]
        if not matches:
            raise ValueError(f"Колонка с '{keyword}' не найдена")
        return matches[0]


# # Пример использования
# parser = ReldParser()
# products = parser.parse()
# for p in products:
#     print(f"Товар: {p['code']} | Название: {p['title']} | Цена: {p['price']}")