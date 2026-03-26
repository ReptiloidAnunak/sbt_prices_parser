import pandas as pd

def get_uriarte_products():
    file_path = 'uriarte.xlsx'
    
    all_sheets = pd.read_excel(file_path, sheet_name=None)
    
    for sheet_name, df in all_sheets.items():
        df.columns = df.columns.str.strip()
        
        target_cols = ['CODIGO UT', 'DESCRIPCION', 'USD LISTA SEPTIEMBRE']
        
        if set(target_cols).issubset(df.columns):
            selected_columns = df[target_cols].dropna(subset=['CODIGO UT'])
            
            print(f"--- Лист: {sheet_name} ---")
            for index, row in selected_columns.iterrows():
                codigo = row['CODIGO UT']
                descripcion = row['DESCRIPCION']
                precio = row['USD LISTA SEPTIEMBRE']
                
                print(f"Товар: {codigo} | Название: {descripcion} | Цена USD: {precio}")
        else:
            continue

get_uriarte_products()