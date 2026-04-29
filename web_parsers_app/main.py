import os
import sys
import django
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api_server.settings")
django.setup()


from web_parsers_app.parsers.ansal import run as run_ansal
from web_parsers_app.parsers.duna import run as run_duna
from web_parsers_app.parsers.electrocity import run as run_electrocity
from web_parsers_app.parsers.electrofrig import run as run_electrofrig
from web_parsers_app.parsers.fijamom import run as run_fijamom
from web_parsers_app.parsers.nordfrig import run as run_nordfrig
from web_parsers_app.parsers.roma import run as run_roma
from web_parsers_app.parsers.reld_retail import run as run_reld_retail
from web_parsers_app.parsers.bellini_retail import run as run_bellini_retail
from web_parsers_app.parsers.refrigeracion_norte_retail import run as run_refrigeracion_norte_retail

import logging


logger = logging.getLogger(__name__)

logger.info("Web parser module is connected")

PARSERS = {
    "ansal": run_ansal,
    "duna": run_duna,
    "electrocity": run_electrocity,
    "electrofrig": run_electrofrig,
    "fijamom": run_fijamom,
    "nordfrig": run_nordfrig,
    "roma": run_roma,
    "reld_retail": run_reld_retail,
    "bellini_retail": run_bellini_retail,
    "refrigeracion_norte_retail": run_refrigeracion_norte_retail,
}


def run_all():
    results = {}

    for name, parser_func in PARSERS.items():
        print(f"🚀 Running parser: {name}")

        try:
            results[name] = parser_func()
        except Exception as e:
            results[name] = f"ERROR: {e}"

    return results


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python web_parsers_app/main.py ansal")
        print("  python web_parsers_app/main.py reld_retail")
        print("  python web_parsers_app/main.py all")
        print("Available parsers:", ", ".join(PARSERS.keys()))
        return

    parser_name = sys.argv[1]

    if parser_name == "all":
        print(run_all())
        return

    parser_func = PARSERS.get(parser_name)

    if not parser_func:
        print(f"Unknown parser: {parser_name}")
        print("Available:", ", ".join(PARSERS.keys()))
        return

    print(parser_func())


if __name__ == "__main__":
    main()