
import pandas as pd

def update_bellini_prices():
    
    file_path = "Lista Comercio 1 30-03-26.xlsx"

    df = pd.read_excel(file_path, header=None)

    header_row = df[
        df.apply(lambda r: r.astype(str).str.contains('Cód. Artículo', case=False).any(), axis=1)
    ].index[0]

    df = pd.read_excel(file_path, header=header_row)

    df.columns = df.columns.astype(str).str.strip()

    print("📊 Колонки:", df.columns.tolist())

    df = df[['Cód. Artículo', 'Descripción', 'PESOS + IVA']]

    df = df.dropna(subset=['Cód. Artículo', 'Descripción'])

    df['PESOS + IVA'] = (
        df['PESOS + IVA']
        .astype(str)
        .str.replace('.', '', regex=False)   # убрать разделители тысяч (если есть)
        .str.replace(',', '.', regex=False)  # заменить запятую на точку
    )

    df['PESOS + IVA'] = pd.to_numeric(df['PESOS + IVA'], errors='coerce')

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