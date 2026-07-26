#!/bin/sh
set -eu

python <<'PY'
import os
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
from django.db import connections
from django.db.utils import OperationalError

django.setup()

attempts = int(os.getenv("DB_WAIT_ATTEMPTS", "30"))
delay = float(os.getenv("DB_WAIT_DELAY", "2"))

print("Waiting for the database...")
for attempt in range(1, attempts + 1):
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
        print("Database is available.")
        break
    except OperationalError as error:
        connections.close_all()
        if attempt == attempts:
            raise SystemExit(
                f"Database is still unavailable after {attempts} attempts: {error}"
            ) from error
        print(f"Database unavailable ({attempt}/{attempts}), retrying in {delay:g}s...")
        time.sleep(delay)
PY

python manage.py migrate --noinput

if [ "${COLLECT_STATIC:-false}" = "true" ]; then
    python manage.py collectstatic --noinput
fi

exec "$@"
