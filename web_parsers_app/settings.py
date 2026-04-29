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
    "nordfrig": DATA_DIR / "nordfrig_products.json",
    "roma": DATA_DIR / "roma_products.json",
    "reld_retail": DATA_DIR / "reld_retail_products.json",
    "bellini_retail": DATA_DIR / "bellini_retail_products.json",
    "refrigeracion_norte_retail": DATA_DIR / "refrigeracion_norte_retail_products.json",
}


SUPPLIER_NAMES = {
    "ansal": "Ansal",
    "duna": "Duna srl",
    "electrocity": "Electrocity",
    "electrofrig": "Electrofrig",
    "fijamom": "Fijamom",
    "nordfrig": "Norfrig",
    "roma": "Roma Repuestos insumos",
    "reld_retail": "Reld",
    "bellini_retail": "Bellini",
    "refrigeracion_norte_retail": "Refrigeracion Norte",
}


def get_json_file(parser_name: str) -> Path:
    return JSON_FILES[parser_name]


def get_json_file_retail(parser_name: str) -> Path:
    return JSON_FILES[parser_name]


def get_supplier_name(parser_name: str) -> str:
    return SUPPLIER_NAMES[parser_name]


def get_screen_shot_path(parser_name):
    screenshot_dir = LOGS_DIR / "screens" / parser_name
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    return screenshot_dir / f"{parser_name}_error.png"