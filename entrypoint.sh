#!/bin/bash

set -e

echo "⏳ Waiting for PostgreSQL..."

python3 << END
import socket
import time

host = "sbt_pars_db"
port = 5432

while True:
    try:
        s = socket.create_connection((host, port), timeout=2)
        s.close()
        break
    except Exception:
        time.sleep(1)
END

echo "✅ PostgreSQL is up!"

echo "🔧 Applying migrations..."
python3 manage.py makemigrations --noinput
python3 manage.py migrate --noinput

echo "👤 Creating superuser if not exists..."

python3 manage.py shell <<EOF
from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass"
    )
    print("Superuser created")
else:
    print("Superuser already exists")
EOF

echo "📦 Loading initial suppliers and products if needed..."

python3 manage.py shell <<EOF
import os
import runpy

init_file = "init_uploads/download_init.py"

if os.path.exists(init_file):
    runpy.run_path(init_file)
    print("Initial data loaded")
else:
    print("No init file found")
EOF

echo "📁 Collecting static files..."
python3 manage.py collectstatic --noinput

echo "🚀 Starting Django server..."
exec python3 manage.py runserver 0.0.0.0:8000