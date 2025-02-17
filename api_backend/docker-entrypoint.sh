#!/bin/bash
set -e

# Проверяем наличие команды docker
if ! command -v docker &> /dev/null; then
    echo "Предупреждение: команда docker не найдена в PATH"
    echo "PATH=$PATH"
fi

# Создаем директорию для бэкапов, если её нет
if [ ! -d /backups ]; then
    mkdir -p /backups || echo "Предупреждение: не удалось создать директорию /backups"
fi

# Запускаем команду
exec "$@"
