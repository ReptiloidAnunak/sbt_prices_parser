#!/bin/bash

BASE_DIR="web_parsers"

for dir in "$BASE_DIR"/*/; do
    if [ -d "$dir" ]; then
        echo "Обрабатываю $dir"

        cd "$dir" || continue

        if [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate

            if [ -f "send_json.py" ]; then
                python3 -m send_json
            else
                echo "⚠️ Нет send_json.py"
            fi

            deactivate
        else
            echo "Нет виртуального окружения"
        fi

        cd - > /dev/null
    fi
done