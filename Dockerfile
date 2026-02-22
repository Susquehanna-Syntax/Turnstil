FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Need these for psycopg2 (PostgreSQL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Collect static files at build time
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Migrate at runtime, then serve
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]