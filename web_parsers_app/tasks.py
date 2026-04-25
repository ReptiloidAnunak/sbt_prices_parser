from celery import shared_task, chain

from web_parsers_app.parsers.ansal import run as run_ansal
from web_parsers_app.parsers.duna import run as run_duna
from web_parsers_app.parsers.electrocity import run as run_electrocity
from web_parsers_app.parsers.electrofrig import run as run_electrofrig
from web_parsers_app.parsers.fijamom import run as run_fijamom
from web_parsers_app.parsers.nordfrig import run as run_nordfrig
from web_parsers_app.parsers.roma import run as run_roma


PARSERS = {
    "duna": run_duna,
    "electrocity": run_electrocity,
    "electrofrig": run_electrofrig,
    "fijamom": run_fijamom,
    "nordfrig": run_nordfrig,
    "roma": run_roma,
    "ansal": run_ansal,
}


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=60,
    retry_kwargs={"max_retries": 3},
    soft_time_limit=1800,
    time_limit=2100,
)
def run_web_parser(self, parser_name):
    parser_func = PARSERS.get(parser_name)

    if not parser_func:
        raise ValueError(f"Unknown parser: {parser_name}")

    return parser_func()


@shared_task
def run_all_web_parsers():
    return chain(
        run_web_parser.si("duna"),
        run_web_parser.si("electrocity"),
        run_web_parser.si("electrofrig"),
        run_web_parser.si("fijamom"),
        run_web_parser.si("nordfrig"),
        run_web_parser.si("roma"),
        run_web_parser.si("ansal"),
    ).apply_async()