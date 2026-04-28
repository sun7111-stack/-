#!/usr/bin/env sh
set -e

python - <<'PY'
import os
import socket
import time

host = os.getenv("DB_HOST", "db")
port = int(os.getenv("DB_PORT", "3306"))
deadline = time.time() + 90

while True:
    try:
        with socket.create_connection((host, port), timeout=3):
            print(f"[docker] database is reachable at {host}:{port}")
            break
    except OSError as exc:
        if time.time() > deadline:
            raise SystemExit(f"[docker] database wait timeout: {exc}")
        print(f"[docker] waiting for database {host}:{port} ...")
        time.sleep(2)
PY

if [ "${RUN_DB_INIT:-true}" = "true" ]; then
  echo "[docker] initializing database schema and seed data"
  python init_db.py
  python migrate_db.py
fi

exec "$@"
