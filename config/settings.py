# settings.py
import os
import sys
import logging
from pathlib import Path
from django.contrib.messages import constants as messages
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Entorno
DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"
ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")  # dev|qa|prd
BASE_DIR = Path(__file__).resolve().parent.parent

# Secret Key
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

# Internacionalización / Zona horaria
LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Hosts / Orígenes
hosts = [
    h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",") if h.strip()
]
ALLOWED_HOSTS = hosts

DEFAULT_SCHEME = "https" if ENVIRONMENT == "prd" else "http"


def _to_origin(h: str) -> str:
    return h if h.startswith(("http://", "https://")) else f"{DEFAULT_SCHEME}://{h}"


CSRF_TRUSTED_ORIGINS = [_to_origin(h) for h in ALLOWED_HOSTS]

# Apps
INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admindocs",
    # Libs
    "django_cotton",
    "crispy_forms",
    "crispy_bootstrap5",
    "django_extensions",
    "import_export",
    "multiselectfield",
    "rest_framework",
    "rest_framework_api_key",
    "corsheaders",
    # Apps propias
    "users",
    "core",
    "dashboard",
    "comedores",
    "organizaciones",
    "cdi",
    "ciudadanos",
    "duplas",
    "admisiones",
    "intervenciones",
    "historial",
    "acompanamientos",
    "expedientespagos",
    "relevamientos",
    "rendicioncuentasfinal",
    "rendicioncuentasmensual",
    "centrodefamilia",
    "celiaquia",
]

# Middleware (orden CORS correcto)
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.admindocs.middleware.XViewMiddleware",
    "config.middlewares.xss_protection.XSSProtectionMiddleware",
    "config.middlewares.threadlocals.ThreadLocalMiddleware",
]

# URLs / WSGI
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# Templates
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Archivos estáticos y media
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "static_root"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Autenticación / Redirecciones
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "inicio"
LOGOUT_REDIRECT_URL = "login"
ACCOUNT_FORMS = {"login": "users.forms.UserLoginForm"}

# Email
if ENVIRONMENT == "prd":
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Mensajes / Crispy
MESSAGE_TAGS = {
    messages.DEBUG: "alert-dark",
    messages.INFO: "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR: "error",
}
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# DB
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("DATABASE_NAME"),
        "USER": os.environ.get("DATABASE_USER"),
        "PASSWORD": os.environ.get("DATABASE_PASSWORD"),
        "HOST": os.environ.get("DATABASE_HOST"),
        "PORT": os.environ.get("DATABASE_PORT"),
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            "charset": "utf8mb4",
        },
        "CONN_MAX_AGE": 60,
    }
}

if "pytest" in sys.argv or os.environ.get("PYTEST_RUNNING") == "1":  # DB para testing
    DATABASES = {
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
    }

# Cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

# TTLs (segundos)
DEFAULT_CACHE_TIMEOUT = 300
DASHBOARD_CACHE_TIMEOUT = 300
COMEDOR_CACHE_TIMEOUT = 300
CIUDADANO_CACHE_TIMEOUT = 300
INTERVENCIONES_CACHE_TIMEOUT = 1800
CENTROFAMILIA_CACHE_TIMEOUT = 300

# CORS
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = CSRF_TRUSTED_ORIGINS

# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}

# Dominios / Integraciones
DOMINIO = os.environ.get("DOMINIO", "localhost:8001")
RENAPER_API_USERNAME = os.getenv("RENAPER_API_USERNAME")
RENAPER_API_PASSWORD = os.getenv("RENAPER_API_PASSWORD")
RENAPER_API_URL = os.getenv("RENAPER_API_URL")

# IPs internas
INTERNAL_IPS = ["127.0.0.1", "::1"]

# Logging (asegurar directorio)
LOG_DIR = BASE_DIR / "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "info_only": {
            "()": "django.utils.log.CallbackFilter",
            "callback": lambda r: r.levelno == logging.INFO,
        },
        "error_only": {
            "()": "django.utils.log.CallbackFilter",
            "callback": lambda r: r.levelno == logging.ERROR,
        },
        "warning_only": {
            "()": "django.utils.log.CallbackFilter",
            "callback": lambda r: r.levelno == logging.WARNING,
        },
        "critical_only": {
            "()": "django.utils.log.CallbackFilter",
            "callback": lambda r: r.levelno == logging.CRITICAL,
        },
        "data_only": {
            "()": "django.utils.log.CallbackFilter",
            "callback": lambda r: hasattr(r, "data"),
        },
    },
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {module} {levelname} {name}: {message}",
            "style": "{",
        },
        "simple": {"format": "[{asctime}] {levelname} {message}", "style": "{"},
        "json_data": {
            "()": "core.utils.JSONDataFormatter",
        },
    },
    "handlers": {
        "info_file": {
            "level": "INFO",
            "filters": ["info_only"],
            "class": "core.utils.DailyFileHandler",
            "filename": str(LOG_DIR / "info.log"),
            "formatter": "verbose",
        },
        "error_file": {
            "level": "ERROR",
            "filters": ["error_only"],
            "class": "core.utils.DailyFileHandler",
            "filename": str(LOG_DIR / "error.log"),
            "formatter": "verbose",
        },
        "warning_file": {
            "level": "WARNING",
            "filters": ["warning_only"],
            "class": "core.utils.DailyFileHandler",
            "filename": str(LOG_DIR / "warning.log"),
            "formatter": "verbose",
        },
        "critical_file": {
            "level": "CRITICAL",
            "filters": ["critical_only"],
            "class": "core.utils.DailyFileHandler",
            "filename": str(LOG_DIR / "critical.log"),
            "formatter": "verbose",
        },
        "data_file": {
            "level": "INFO",
            "filters": ["data_only"],
            "class": "core.utils.DailyFileHandler",
            "filename": str(LOG_DIR / "data.log"),
            "formatter": "json_data",
        },
    },
    "loggers": {
        "django": {
            "handlers": [
                "info_file",
                "error_file",
                "warning_file",
                "critical_file",
                "data_file",
            ],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["error_file"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}

# Validadores de contraseña
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Herramientas debug/perf en desarrollo
if DEBUG:
    INSTALLED_APPS += ["debug_toolbar", "silk"]
    MIDDLEWARE.insert(
        3, "debug_toolbar.middleware.DebugToolbarMiddleware"
    )  # index tras Cors/Common
    MIDDLEWARE += ["silk.middleware.SilkyMiddleware"]
    DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda request: True}
    SILKY_PYTHON_PROFILER = True

# Seguridad por entorno
if ENVIRONMENT == "prd":
    STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
    )
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    USE_X_FORWARDED_HOST = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
else:
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# Config propia (constantes)
PROG_MILD = 24
PROG_CDIF = 23
PROG_CDLE = 25
PROG_PDV = 26
PROG_MA = 30
PROG_SL = 21
