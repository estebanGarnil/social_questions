# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .
RUN chmod +x /app/docker/backend/entrypoint.sh

FROM base AS development
ENTRYPOINT ["/app/docker/backend/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM base AS production

RUN groupadd --gid 10001 app \
    && useradd \
        --uid 10001 \
        --gid app \
        --no-create-home \
        --home-dir /app \
        --shell /usr/sbin/nologin \
        app \
    && mkdir -p /app/staticfiles /app/media \
    && chown -R app:app /app/staticfiles /app/media

USER app

ENTRYPOINT ["/app/docker/backend/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60"]