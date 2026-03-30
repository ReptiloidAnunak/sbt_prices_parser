import pandas as pd


def update_belgrano_prices():
    file = "belgrano.xlsx"

    df_raw = pd.read_excel(file, header=None)

    header_row = None
    for i, row in df_raw.iterrows():
        row_str = row.astype(str).str.lower()
        if row_str.str.contains("cod").any():
            header_row = i
            break

    df = pd.read_excel(file, header=header_row)

    df.columns = df.columns.str.strip().str.lower()

    col_codigo = [c for c in df.columns if "cod" in c][0]

    # индекс колонки кода
    idx = df.columns.get_loc(col_codigo)

    # продукт = следующая колонка справа
    col_producto = df.columns[idx + 1]

    # цена = колонка с precio + iva
    col_precio = [c for c in df.columns if "precio" in c and "iva" in c][0]

    # пытаемся найти колонку с валютой
    possible_currency_cols = [c for c in df.columns if any(k in c for k in ["moneda", "usd", "currency", "$"])]
    if possible_currency_cols:
        col_moneda = possible_currency_cols[0]
    else:
        col_moneda = None

    # собираем колонки
    if col_moneda:
        result = df[[col_codigo, col_producto, col_moneda, col_precio]].copy()
        result.columns = ["Cod Producto", "Producto", "Moneda", "Precio De Venta Con Iva"]
    else:
        result = df[[col_codigo, col_producto, col_precio]].copy()
        result.columns = ["Cod Producto", "Producto", "Precio De Venta Con Iva"]
        result["Moneda"] = "ARS"  # или "USD", если знаешь

    # убираем мусор (где продукт = код)
    result = result[result["Producto"] != result["Cod Producto"]]
    result = result.dropna()

    result.to_excel("productos_limpios_fixed.xlsx", index=False)

    print("Готово: productos_limpios_fixed.xlsx")