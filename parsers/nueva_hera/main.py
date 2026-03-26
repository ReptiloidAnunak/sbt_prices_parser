import pandas as pd
import re
import os

def get_listado_products():
    folder_path = 'price_lists'
    if not os.path.exists(folder_path):
        print(f"Папка {folder_path} не найдена")
        return

    files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.xlsx')]

    for file_path in files:
        try:
            df = pd.read_excel(file_path, header=None)
            print(f"\n=== Обработка файла: {file_path} ===")

            for index, row in df.iterrows():
                # Переводим всю строку в список строк
                row_values = [str(val).strip() if pd.notna(val) else "" for val in row]
                
                # Если строка совсем пустая — скипаем
                if not any(row_values):
                    continue

                # 1. Ищем КОД (теперь проверяем индексы 0 И 1)
                # Код — это либо слово "Cod", либо просто число (как 701, 702)
                code_idx = -1
                for i in [0, 1]:
                    if i < len(row_values):
                        val = row_values[i]
                        if "cod" in val.lower() or (val and val.isdigit()):
                            code_idx = i
                            break
                
                if code_idx == -1:
                    continue

                # 2. Ищем ЦЕНУ (ищем ячейку, где есть "u$s" или цифры в конце строки)
                price_idx = -1
                for i in range(len(row_values)-1, code_idx, -1):
                    val = row_values[i].lower()
                    if "u$s" in val or (val and any(c.isdigit() for c in val)):
                        price_idx = i
                        break
                
                if price_idx == -1 or price_idx <= code_idx:
                    continue

                # 3. Собираем НАЗВАНИЕ (все что между кодом и ценой)
                desc_parts = [row_values[i] for i in range(code_idx + 1, price_idx) if row_values[i]]
                final_description = " ".join(desc_parts)

                # 4. Чистим ЦЕНУ
                raw_precio = row_values[price_idx]
                clean_price = re.sub(r'[^\d,.]', '', raw_precio).replace(',', '.')
                try:
                    float_price = float(clean_price) if clean_price else 0.0
                except:
                    float_price = 0.0

                # Выводим результат, если есть описание или код выглядит валидно
                if final_description or len(row_values[code_idx]) > 0:
                    print(f"Код: {row_values[code_idx]} | Название: {final_description} | Цена: {float_price}")
        
        except Exception as e:
            print(f"Ошибка в {file_path}: {e}")

get_listado_products()