import os
import logging
from pathlib import Path
import sys
from django.contrib.messages import constants as messages
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Definición de entorno
DEBUG = os.environ.get("DJANGO_DEBUG", default=False) == "True"
ENVIRONMENT = os.environ.get("ENVIRONMENT", default="dev")

# Definición del directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Configuración de rutas de estaticos y  media
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "static_root"
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"


MEDIA_URL = "media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media/")


# Configuración de URLs para autenticación
LOGIN_URL = "/"
LOGIN_REDIRECT_URL = "dashboard/"
LOGOUT_REDIRECT_URL = "/"

# Formularios personalizados para cuentas de usuario
ACCOUNT_FORMS = {"login": "user.forms.UserLoginForm"}

# Configuración de backend de correo electrónico
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Configuración de etiquetas de mensajes
MESSAGE_TAGS = {
    messages.DEBUG: "alert-dark",
    messages.INFO: "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR: "error",
}


# Configuración de clases CSS para formularios Crispy
CRISPY_CLASS_CONVERTERS = {
    "textinput": "form-control",
    "passwordinput": "form-control",
    "select": "form-control custom-select",
    "selectmultiple": "form-control select2 w-100",
    "numberinput": "form-control",
    "emailinput": "form-control",
    "dateinput": "form-control",
    "fileinput": "custom-file-input",
}

# Definición de variables de programas
PROG_MILD = 24
PROG_CDIF = 23
PROG_CDLE = 25
PROG_PDV = 26
PROG_MA = 30
PROG_SL = 21

# Definición de IPs internas para depuración
INTERNAL_IPS = [
    "127.0.0.1",
    "::1",
]

# Configuración de la aplicación WSGI
WSGI_APPLICATION = "config.wsgi.application"

# Configuración de localización
LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True

# Configuración de campo auto por defecto
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Obtención de la clave secreta desde variables de entorno
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

# Configuración del paquete de plantillas Crispy
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Configuración de la URLs
ROOT_URLCONF = "config.urls"

# Configuración de hosts permitidos desde variables de entorno
hosts = os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")
ALLOWED_HOSTS = hosts

# Configuración de CSRF
CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in hosts]
CSRF_COOKIE_NAME = (
    "csrftoken_v2"  # Cambiar en caso de conflicto con formularios cacheados
)

# Configuración para cerrar la sesión al cerrar el navegador
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Definición de aplicaciones instaladas
INSTALLED_APPS = [
    # Aplicaciones de Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admindocs",
    # Librerias
    "django_cotton",
    "crispy_forms",
    "crispy_bootstrap5",
    "django_extensions",
    "import_export",
    "multiselectfield",
    "rest_framework",
    "rest_framework_api_key",
    "corsheaders",
    # Aplicaciones propias
    "users",
    "core",
    "configuraciones",
    "dashboard",
    "comedores",
    "organizaciones",
    "provincias",
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
]

# Definición del middleware utilizado por el proyecto
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.admindocs.middleware.XViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "config.middlewares.xss_protection.XSSProtectionMiddleware",
    "config.middlewares.threadlocals.ThreadLocalMiddleware",
    "corsheaders.middleware.CorsMiddleware",
]

# Configuración de plantillas
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

# Configuración de la base de datos
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
if "pytest" in sys.argv:  # DB para testing
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }


# Configuración de Cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

# Configuración global de tiempos de cache (en segundos)
DEFAULT_CACHE_TIMEOUT = 300  # 5 minutos por defecto
DASHBOARD_CACHE_TIMEOUT = 300  # 5 minutos para dashboard
COMEDOR_CACHE_TIMEOUT = 300  # 5 minutos para comedores
CIUDADANO_CACHE_TIMEOUT = 300  # 5 minutos para ciudadanos
INTERVENCIONES_CACHE_TIMEOUT = (
    1800  # 30 minutos para tipos de intervención (cambian poco)
)
CENTROFAMILIA_CACHE_TIMEOUT = 300  # 5 minutos para centro de familia


# Configuracion de logging
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
    },
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {module} {levelname} {name}: {message}",
            "style": "{",
        },
        "simple": {
            "format": "[{asctime}] {levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "info_file": {
            "level": "INFO",
            "filters": ["info_only"],
            "class": "core.utils.DailyFileHandler",
            "filename": str(BASE_DIR / "logs/info.log"),
            "formatter": "verbose",
        },
        "error_file": {
            "level": "ERROR",
            "filters": ["error_only"],
            "class": "core.utils.DailyFileHandler",
            "filename": str(BASE_DIR / "logs/error.log"),
            "formatter": "verbose",
        },
        "warning_file": {
            "level": "WARNING",
            "filters": ["warning_only"],
            "class": "core.utils.DailyFileHandler",
            "filename": str(BASE_DIR / "logs/warning.log"),
            "formatter": "verbose",
        },
        "critical_file": {
            "level": "CRITICAL",
            "filters": ["critical_only"],
            "class": "core.utils.DailyFileHandler",
            "filename": str(BASE_DIR / "logs/critical.log"),
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": [
                "info_file",
                "error_file",
                "warning_file",
                "critical_file",
            ],
            "level": "DEBUG",
            "propagate": True,
        },
        "django.request": {
            "handlers": [
                "error_file"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}

# Configuración de validadores de contraseñas
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Configuraciones de entornos
if DEBUG:

    # Configuración de Django Debug Toolbar
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
    DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda request: True}

    # Configuración de Silk fuera de DEBUG
    INSTALLED_APPS += ["silk"]
    MIDDLEWARE += ["silk.middleware.SilkyMiddleware"]
    SILKY_PYTHON_PROFILER = True

if ENVIRONMENT == "prd":
    # Configuración para producción
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
else:
    # Configuración para entornos bajos (no ssl)
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# Configuracion de Django Rest Framework
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}

# Configuracion de CORS header
CORS_ALLOW_ALL_ORIGINS = True

# Configuracion de dominio para API GESTIONAR
DOMINIO = os.environ.get("DOMINIO", default="localhost:8001")

# API RENAPER
RENAPER_API_USERNAME = os.getenv("RENAPER_API_USERNAME")
RENAPER_API_PASSWORD = os.getenv("RENAPER_API_PASSWORD")
RENAPER_API_URL = os.getenv("RENAPER_API_URL")