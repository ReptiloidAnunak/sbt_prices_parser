#!/bin/sh
set -e

python - <<'PY'
import socket
import time

services = [("sbt_pars_db", 5432), ("redis", 6379)]
for host, port in services:
    while True:
        try:
            with socket.create_connection((host, port), timeout=2):
                print(f"{host}:{port} is ready")
                break
        except OSError:
            print(f"Waiting for {host}:{port}...")
            time.sleep(2)
PY

exec "$@"