#!/bin/bash

BASE_DIR="web_parsers"

for dir in "$BASE_DIR"/*/; do
    if [ -d "$dir" ]; then
        echo "Обрабатываю $dir"

        cd "$dir" || continue

        if [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate
            python3 -m send_json
            deactivate
        else
            echo "Нет виртуального окружения в $dir"
        fi

        cd - > /dev/null
    fi
done