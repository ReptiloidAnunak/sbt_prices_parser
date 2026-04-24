from celery import shared_task

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


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=60,
    retry_kwargs={"max_retries": 3},
    soft_time_limit=600,
    time_limit=900,
)
def run_web_parser(self, parser_name):
    parser_func = PARSERS.get(parser_name)

    if not parser_func:
        raise ValueError(f"Unknown parser: {parser_name}")

    return parser_func()


@shared_task
def run_all_web_parsers():
    result = {}

    for parser_name in PARSERS:
        try:
            result[parser_name] = run_web_parser(parser_name)
        except Exception as e:
            result[parser_name] = f"ERROR: {e}"

    return result