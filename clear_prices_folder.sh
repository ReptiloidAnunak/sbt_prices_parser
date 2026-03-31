#!/bin/bash

FOLDER="media/price_lists"

if [ ! -d "$FOLDER" ]; then
    echo "Папка $FOLDER не найдена, создаём..."
    mkdir -p "$FOLDER"
else
    echo "Удаляем папку $FOLDER вместе с содержимым..."
    rm -rf "$FOLDER"
    echo "Создаём пустую папку $FOLDER..."
    mkdir -p "$FOLDER"
fi

echo "Очистка завершена."