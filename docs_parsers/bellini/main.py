import pandas as pd

file_path = "Lista Comercio 1 30-03-26.xlsx"

# 1. читаем без заголовков
df = pd.read_excel(file_path, header=None)

# 2. ищем строку с заголовками (где есть "Cód. Artículo")
header_row = df[
    df.apply(lambda r: r.astype(str).str.contains('Cód. Artículo', case=False).any(), axis=1)
].index[0]

# 3. перечитываем с правильным header
df = pd.read_excel(file_path, header=header_row)

# 4. чистим названия колонок
df.columns = df.columns.astype(str).str.strip()

print("📊 Колонки:", df.columns.tolist())

# 5. выбираем нужные
df = df[['Cód. Artículo', 'Descripción', 'PESOS + IVA']]

# 6. убираем пустые строки
df = df.dropna(subset=['Cód. Artículo', 'Descripción'])

# 7. чистим цену
df['PESOS + IVA'] = (
    df['PESOS + IVA']
    .astype(str)
    .str.replace('.', '', regex=False)   # убрать разделители тысяч (если есть)
    .str.replace(',', '.', regex=False)  # заменить запятую на точку
)

# иногда там могут быть не числа
df['PESOS + IVA'] = pd.to_numeric(df['PESOS + IVA'], errors='coerce')

# 8. собираем список
productos = []

for _, row in df.iterrows():
    code = str(row['Cód. Artículo']).strip()
    desc = str(row['Descripción']).strip()
    price = row['PESOS + IVA']

    if not desc or desc == '...':
        continue

    productos.append({
        'code': code,
        'description': desc,
        'price_pesos_iva': price
    })

print(productos)
print(f"✅ Всего: {len(productos)}")