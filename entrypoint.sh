#!/bin/bash

set -e

echo "⏳ Waiting for PostgreSQL..."

python3 << END
import socket
import time

while True:
    try:
        s = socket.create_connection(("sbt_pars_db", 5432), timeout=2)
        s.close()
        break
    except Exception:
        time.sleep(1)
END

echo "✅ PostgreSQL is up!"

python3 manage.py makemigrations --noinput
python3 manage.py migrate

echo "👤 Creating superuser (if not exists)..."

python3 manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')

EOF

echo "📦 Loading suppliers and products ..."

python3 manage.py shell <<EOF
import runpy
runpy.run_path("init_uploads/download_init.py")

EOF

python3 manage.py collectstatic --noinput

echo "🚀 Starting server..."
exec python3 manage.py runserver 0.0.0.0:8000