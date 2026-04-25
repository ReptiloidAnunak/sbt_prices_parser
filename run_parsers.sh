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
else
  echo "▶ Running parser: $PARSER"
  docker compose exec sbt_pars_server python manage.py shell -c "
from web_parsers_app.tasks import run_web_parser
run_web_parser.delay('$PARSER')
"
fi

echo "📡 Watching logs..."
docker logs -f sbt_pars_celery_worker