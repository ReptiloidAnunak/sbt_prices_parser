import sys

from web_parsers_app.parsers.ansal import run as run_ansal
from web_parsers_app.parsers.duna import run as run_duna
from web_parsers_app.parsers.electrocity import run as run_electrocity
from web_parsers_app.parsers.electrofrig import run as run_electrofrig
from web_parsers_app.parsers.fijamom import run as run_fijamom
from web_parsers_app.parsers.nordfrig import run as run_nordfrig
from web_parsers_app.parsers.roma import run as run_roma


PARSERS = {
    "ansal": run_ansal,
    "duna": run_duna,
    "electrocity": run_electrocity,
    "electrofrig": run_electrofrig,
    "fijamom": run_fijamom,
    "nordfrig": run_nordfrig,
    "roma": run_roma,
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
        print("  python main.py ansal")
        print("  python main.py all")
        print("Available parsers:", ", ".join(PARSERS.keys()))
        return

    parser_name = sys.argv[1]

    if parser_name == "all":
        result = run_all()
        print(result)
        return

    parser_func = PARSERS.get(parser_name)

    if not parser_func:
        print(f"Unknown parser: {parser_name}")
        print("Available:", ", ".join(PARSERS.keys()))
        return

    result = parser_func()
    print(result)


if __name__ == "__main__":
    main()