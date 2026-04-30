from celery import shared_task, chain
from django.utils import timezone

from web_parsers_app.parsers.ansal import run as run_ansal
from web_parsers_app.parsers import ansal_retail
from web_parsers_app.parsers.duna import run as run_duna
from web_parsers_app.parsers.electrocity import run as run_electrocity
from web_parsers_app.parsers.electrofrig import run as run_electrofrig
from web_parsers_app.parsers.fijamom import run as run_fijamom
from web_parsers_app.parsers.nordfrig import run as run_nordfrig
from web_parsers_app.parsers.roma import run as run_roma
from web_parsers_app.parsers.reld_retail import run as run_reld_retail
from web_parsers_app.parsers.bellini_retail import run as run_bellini_retail
from web_parsers_app.parsers.refrigeracion_norte_retail import run as run_refrigeracion_norte_retail

PARSERS = {
    "duna": run_duna,
    "electrocity": run_electrocity,
    "electrofrig": run_electrofrig,
    "fijamom": run_fijamom,
    "nordfrig": run_nordfrig,
    "roma": run_roma,
    "reld_retail": run_reld_retail,
    "bellini_retail": run_bellini_retail,
    "refrigeracion_norte_retail": run_refrigeracion_norte_retail,
    "ansal_retail": ansal_retail.run,
}


def _mark_started(parser_name):
    try:
        from web_parsers_app.models import ParserJob
        ParserJob.objects.filter(name=parser_name).update(
            last_run_at=timezone.now(),
            last_status="RUNNING",
            last_error="",
        )
    except Exception:
        pass


def _mark_success(parser_name, result):
    try:
        from web_parsers_app.models import ParserJob
        ParserJob.objects.filter(name=parser_name).update(
            last_success_at=timezone.now(),
            last_status="SUCCESS",
            last_result=result,
            last_error="",
        )
    except Exception:
        pass


def _mark_error(parser_name, error):
    try:
        from web_parsers_app.models import ParserJob
        ParserJob.objects.filter(name=parser_name).update(
            last_status="ERROR",
            last_error=str(error),
        )
    except Exception:
        pass


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

    _mark_started(parser_name)

    try:
        result = parser_func()
        _mark_success(parser_name, result)
        return result
    except Exception as e:
        _mark_error(parser_name, e)
        raise


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=60,
    retry_kwargs={"max_retries": 3},
    soft_time_limit=36000,  # 10 часов для Ansal
    time_limit=36600,      # 10 часов 10 минут hard limit
)
def run_ansal_parser(self):
    parser_name = "ansal"
    _mark_started(parser_name)

    try:
        result = run_ansal()
        _mark_success(parser_name, result)
        return result
    except Exception as e:
        _mark_error(parser_name, e)
        raise


@shared_task
def run_all_web_parsers():
    return chain(
        run_web_parser.si("duna"),
        run_web_parser.si("electrocity"),
        run_web_parser.si("electrofrig"),
        run_web_parser.si("fijamom"),
        run_web_parser.si("nordfrig"),
        run_web_parser.si("roma"),
        run_web_parser.si("reld_retail"),
        run_ansal_parser.si(),
        run_web_parser.si("ansal_retail"),
    ).apply_async()