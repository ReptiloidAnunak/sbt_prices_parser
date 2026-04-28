#!/bin/bash

set -e

echo "🚀 Starting parsers..."

PARSER=${1:-all}

if [ "$PARSER" = "all" ]; then
  echo "🔄 Running ALL parsers sequentially..."
  docker compose exec sbt_pars_server python manage.py shell -c "
from web_parsers_app.tasks import run_all_web_parsers
run_all_web_parsers.delay()
"
elif [ "$PARSER" = "ansal" ]; then
  echo "▶ Running long parser: ansal"
  docker compose exec sbt_pars_server python manage.py shell -c "
from web_parsers_app.tasks import run_ansal_parser
run_ansal_parser.delay()
"
else
  echo "▶ Running parser: $PARSER"
  docker compose exec sbt_pars_server python manage.py shell -c "
from web_parsers_app.tasks import run_web_parser
run_web_parser.delay('$PARSER')
"
fi

echo "📡 Watching logs..."
docker logs --tail=100 -f sbt_pars_celery_worker