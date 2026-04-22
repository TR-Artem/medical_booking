FROM python:3.12-slim

# Системные зависимости
RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Зависимости Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Исходный код
COPY . .

# Статические файлы
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["gunicorn", "medical_booking.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
