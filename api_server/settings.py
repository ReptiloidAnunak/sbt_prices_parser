"""
Django settings for api_server project.
"""

from pathlib import Path
from celery.schedules import crontab
import os


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-m-xe_d=l#5=@#v^+aqg2l*fg-l_71du#xa)g12*hedn+annvw(",
)

DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"

ALLOWED_HOSTS = [
    h for h in os.getenv(
        "DJANGO_ALLOWED_HOSTS",
        "localhost,127.0.0.1,0.0.0.0,sbt_pars_server,testserver",
    ).split(",")
    if h
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "supplier.apps.SupplierConfig",
    "product.apps.ProductConfig",
    "mercado_libre.apps.MercadoLibreConfig",
    "options.apps.OptionsConfig",
    "web_parsers_app.apps.WebParsersAppConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "api_server.urls"

# ВАЖНО:
# Для кастомных шаблонов админки, например:
# templates/admin/product/product/change_list.html
# нужна строка DIRS: [BASE_DIR / "templates"]
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "api_server.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "postgres"),
        "USER": os.getenv("POSTGRES_USER", "postgres"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.getenv("POSTGRES_HOST", "sbt_pars_db"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CATEGORIES_FILE = BASE_DIR / "product" / "categories.json"

# ---------------- CELERY ----------------

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

CELERY_TIMEZONE = "America/Argentina/Buenos_Aires"
CELERY_ENABLE_UTC = False

CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_RETRY = True
CELERY_BROKER_TRANSPORT_OPTIONS = {
    "visibility_timeout": 12 * 60 * 60,
    "socket_keepalive": True,
    "socket_connect_timeout": 30,
}

CELERY_BEAT_SCHEDULE = {
    "run-duna-every-night": {
        "task": "web_parsers_app.tasks.run_web_parser",
        "schedule": crontab(hour=1, minute=0),
        "args": ("duna",),
    },
    "run-electrocity-every-night": {
        "task": "web_parsers_app.tasks.run_web_parser",
        "schedule": crontab(hour=1, minute=30),
        "args": ("electrocity",),
    },
    "run-electrofrig-every-night": {
        "task": "web_parsers_app.tasks.run_web_parser",
        "schedule": crontab(hour=2, minute=0),
        "args": ("electrofrig",),
    },
    "run-fijamom-every-night": {
        "task": "web_parsers_app.tasks.run_web_parser",
        "schedule": crontab(hour=2, minute=30),
        "args": ("fijamom",),
    },
    "run-nordfrig-every-night": {
        "task": "web_parsers_app.tasks.run_web_parser",
        "schedule": crontab(hour=3, minute=0),
        "args": ("nordfrig",),
    },
    "run-reld-retail-every-night": {
        "task": "web_parsers_app.tasks.run_web_parser",
        "schedule": crontab(hour=3, minute=15),
        "args": ("reld_retail",),
    },
    "run-roma-every-night": {
        "task": "web_parsers_app.tasks.run_web_parser",
        "schedule": crontab(hour=3, minute=30),
        "args": ("roma",),
    },
    "run-ansal-every-night": {
        "task": "web_parsers_app.tasks.run_ansal_parser",
        "schedule": crontab(hour=4, minute=0),
        "args": (),
    },
}

# ---------------- LOGGING ----------------

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": str(LOG_DIR / "server.log"),
        },
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["file", "console"],
        "level": "INFO",
    },
}

DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024