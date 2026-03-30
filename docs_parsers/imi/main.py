import pandas as pd
import re
import os

files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.xlsx')]


def get_listado_products():
    folder_path = 'price_lists'
    if not os.path.exists(folder_path):
        print(f"Папка {folder_path} не найдена")
        return

