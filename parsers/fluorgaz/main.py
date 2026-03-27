import pandas as pd

df = pd.read_excel('fluorgaz.xlsx', header=None)
header_row = df[df.apply(lambda r: r.astype(str).str.contains('PRODUCTO').any(), axis=1)].index[0]
df = pd.read_excel('fluorgaz.xlsx', header=header_row)
df.columns = df.columns.astype(str).str.strip()
df = df[['PRODUCTO', 'PRECIO USD X UNIDAD']]
df = df.dropna(subset=['PRODUCTO', 'PRECIO USD X UNIDAD'])
df['PRECIO USD X UNIDAD'] = (
    df['PRECIO USD X UNIDAD']
    .astype(str)
    .str.replace(',', '.', regex=False)
    .astype(float)
)

productos = []

for _, row in df.iterrows():
    producto = str(row['PRODUCTO']).strip()
    precio = row['PRECIO USD X UNIDAD']

    if producto and producto != '...':
        productos.append({
            'producto': producto,
            'precio_usd': precio
        })


print(productos)