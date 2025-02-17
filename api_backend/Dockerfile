FROM python:3.10-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    tzdata \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Установка временной зоны
ENV TZ=Asia/Aqtau
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Установка Docker CLI
RUN curl -fsSL https://get.docker.com -o get-docker.sh \
    && sh get-docker.sh \
    && rm get-docker.sh

# Создание директорий
RUN mkdir -p /app /backups /app/celerybeat

# Установка рабочей директории
WORKDIR /app

# Установка зависимостей Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода приложения
COPY . .

# Создание директории для бэкапов и установка прав
RUN mkdir -p /backups && \
    chmod 755 /backups && \
    chmod 755 scripts/backup_db.sh

# Установка прав доступа для всех файлов и директорий в /app
RUN chmod -R 777 /app

# Установка переменных окружения для Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Открыть порт для Django
EXPOSE 8000

# Команда по умолчанию
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "api_backend.asgi:application"]
