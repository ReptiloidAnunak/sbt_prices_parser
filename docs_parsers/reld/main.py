import pandas as pd

def get_reld_products():
    file_path = 'reld.xlsx'
    df = pd.read_excel(file_path, skiprows=4)
    df.columns = df.columns.str.strip()
    selected_columns = df[['Codigo', 'Descripcion', 'Precio S/IVA']]
    for index, row in selected_columns.iterrows():
        codigo = row['Codigo']
        descripcion = row['Descripcion']
        precio = row['Precio S/IVA']
        print(f"Товар: {codigo} | Название: {descripcion} | Цена: {precio}")


get_reld_products()