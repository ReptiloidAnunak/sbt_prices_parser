#!/bin/bash

BASE_DIR="web_parsers"
MAX_JOBS=3

running=0

for dir in "$BASE_DIR"/*/; do
    (
        echo "🚀 Запуск: $dir"
        cd "$dir" || exit

        # активируем виртуалку если есть
        if [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate
        fi

        # запускаем скрипт
        if [ -f "load_json.py" ]; then
            python load_json.py
        else
            echo "⚠️ load_json.py не найден в $dir"
        fi
    ) &

    ((running++))

    if [ "$running" -ge "$MAX_JOBS" ]; then
        wait
        running=0
    fi
done

wait
echo "✅ Всё завершено"