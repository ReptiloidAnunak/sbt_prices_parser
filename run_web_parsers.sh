#!/bin/bash

BASE_DIR="web_parsers"
MAX_JOBS=3

running=0

for dir in "$BASE_DIR"/*/; do
    (
        echo "🚀 $dir"
        cd "$dir" || exit

        source .venv/bin/activate 2>/dev/null

        if [ -f "run_docker.sh" ]; then
            ./run_docker.sh
        fi
    ) &

    ((running++))

    if [ "$running" -ge "$MAX_JOBS" ]; then
        wait
        ((running--))
    fi
done

wait
echo "✅ Всё завершено"