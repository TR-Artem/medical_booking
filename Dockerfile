FROM python:3.12-slim

# Системные зависимости
RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Непривилегированный пользователь (P-07): не работаем от root
RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

# Зависимости Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Исходный код
COPY . .

# Статические файлы
RUN python manage.py collectstatic --noinput && chown -R app:app /app

USER app

EXPOSE 8000

CMD ["gunicorn", "medical_booking.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
