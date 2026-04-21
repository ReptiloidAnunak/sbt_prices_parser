from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR /'data'

JSON_FILE = DATA_DIR / "ansal_products.json"
SUPPLIER_NAME = "Ansal"