#!/bin/bash
set -e

# Параметры базы данных
DB_HOST="${POSTGRES_HOST:-db}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-postgres}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_PASSWORD="${POSTGRES_PASSWORD:-postgres}"

# Директория для бэкапов
BACKUP_DIR="/backups"
TIMESTAMP=$(date "+%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="${BACKUP_DIR}/bpm_database_backup_${TIMESTAMP}.dump"

# Проверка наличия директории бэкапов
if [ ! -d "$BACKUP_DIR" ]; then
    echo "Создание директории для бэкапов..."
    mkdir -p "$BACKUP_DIR"
fi

# Создание бэкапа
echo "Создание бэкапа базы данных ${DB_NAME}..."
PGPASSWORD="$DB_PASSWORD" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -F c \
    -b \
    -v \
    -f "$BACKUP_FILE"

# Установка базовых прав на файл бэкапа
chmod 644 "$BACKUP_FILE"

# Очистка старых бэкапов (оставляем файлы не старше 7 дней)
find "$BACKUP_DIR" -name "bpm_database_backup_*.dump" -type f -mtime +7 -delete

echo "Бэкап успешно создан: $BACKUP_FILE"

# Инструкция по восстановлению
echo "Для восстановления используйте команду:"
echo "pg_restore --jobs=4 --clean --dbname=${DB_NAME} --username=${DB_USER} ${BACKUP_FILE}"
