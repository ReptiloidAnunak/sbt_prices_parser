from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

WEB_PARSERS_DIR = PROJECT_DIR / "web_parsers_app"
DATA_DIR = WEB_PARSERS_DIR / "data"
LOGS_DIR = PROJECT_DIR / "logs" / "parsers"

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


JSON_FILES = {
    "ansal": DATA_DIR / "ansal_products.json",
    "duna": DATA_DIR / "duna_products.json",
    "electrocity": DATA_DIR / "electrocity_products.json",
    "electrofrig": DATA_DIR / "electrofrig_products.json",
    "fijamom": DATA_DIR / "fijamom_products.json",
    "norfrig": DATA_DIR / "norfrig_products.json",
    "roma": DATA_DIR / "roma_products.json",
}


SUPPLIER_NAMES = {
    "ansal": "Ansal",
    "duna": "Duna",
    "electrocity": "Electrocity",
    "electrofrig": "Electrofrig",
    "fijamom": "Fijamom",
    "norfrig": "Norfrig",
    "roma": "Roma",
}


# --- helpers ---

def get_json_file(parser_name: str) -> Path:
    return JSON_FILES[parser_name]


def get_supplier_name(parser_name: str) -> str:
    return SUPPLIER_NAMES[parser_name]