# settings.py
import os
import sys
import logging
import tempfile
from pathlib import Path
from django.contrib.messages import constants as messages
from django.utils.module_loading import import_string
from dotenv import load_dotenv
from config.runtime import is_running_tests

# Cargar variables de entorno
load_dotenv()

# Entorno
ENVIRONMENT_ALIASES = {
    "hml": "homologacion",
    "prod": "prd",
    "production": "prd",
}
RAW_ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev").strip().lower()
ENVIRONMENT = ENVIRONMENT_ALIASES.get(RAW_ENVIRONMENT, RAW_ENVIRONMENT)
# dev|qa|homologacion|prd
PRODUCTION_LIKE_ENVIRONMENTS = {"homologacion", "prd"}
IS_PRODUCTION_LIKE_ENVIRONMENT = ENVIRONMENT in PRODUCTION_LIKE_ENVIRONMENTS
DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"
GESTIONAR_INTEGRATION_ENABLED = IS_PRODUCTION_LIKE_ENVIRONMENT
ENABLE_API_DOCS = True
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

DEFAULT_SCHEME = "https" if IS_PRODUCTION_LIKE_ENVIRONMENT else "http"


def _to_origin(h: str) -> str:
    return h if h.startswith(("http://", "https://")) else f"{DEFAULT_SCHEME}://{h}"


def _safe_int_env(var_name: str, default: int) -> int:
    raw_value = os.getenv(var_name)
    if raw_value is None or raw_value.strip() == "":
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


def _safe_float_env(var_name: str, default: float) -> float:
    raw_value = os.getenv(var_name)
    if raw_value is None or raw_value.strip() == "":
        return default
    try:
        return float(raw_value)
    except ValueError:
        return default


def _safe_bool_env(var_name: str, default: bool) -> bool:
    raw_value = os.getenv(var_name)
    if raw_value is None or raw_value.strip() == "":
        return default

    normalized = raw_value.strip().lower()
    if normalized in ("1", "true", "yes", "on"):
        return True
    if normalized in ("0", "false", "no", "off"):
        return False
    return default


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
    "crispy_forms",
    "crispy_bootstrap5",
    "django_extensions",
    "import_export",
    "multiselectfield",
    "auditlog",
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_api_key",
    "drf_spectacular",
    "corsheaders",
    # Apps propias
    "users",
    "core",
    "sentry.apps.SentryConfig",
    "dashboard",
    "comedores",
    "organizaciones",
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
    "VAT",
    "celiaquia",
    "audittrail",
    "importarexpediente",
    "comunicados",
    "centrodeinfancia",
    "pwa",
]

# Middleware (orden CORS correcto)
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "users.middleware.FirstLoginPasswordChangeMiddleware",
    "sentry.middleware.SentryUserContextMiddleware",
    "auditlog.middleware.AuditlogMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.admindocs.middleware.XViewMiddleware",
    "config.middlewares.xss_protection.XSSProtectionMiddleware",
    "config.middlewares.csp.ContentSecurityPolicyMiddleware",
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
                "sentry.context_processors.sentry_frontend",
                "core.context_processors.footer_version",
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
INITIAL_PASSWORD_MAX_AGE_HOURS = _safe_int_env("INITIAL_PASSWORD_MAX_AGE_HOURS", 336)
PASSWORD_RESET_TIMEOUT = _safe_int_env("PASSWORD_RESET_TIMEOUT", 3600)

# Email
settings_logger = logging.getLogger(__name__)

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "").strip()
if not EMAIL_BACKEND:
    # Fallback seguro por defecto: no rompe entornos sin .env o sin SMTP válido.
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

try:
    import_string(EMAIL_BACKEND)
except Exception:  # pragma: no cover - fallback defensivo de configuración
    settings_logger.warning(
        "EMAIL_BACKEND inválido (%s). Se usa backend de consola.",
        EMAIL_BACKEND,
    )
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

EMAIL_HOST = os.getenv("EMAIL_HOST", "").strip() or "localhost"
EMAIL_PORT = _safe_int_env("EMAIL_PORT", 587)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = _safe_bool_env("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = _safe_bool_env("EMAIL_USE_SSL", False)
EMAIL_TIMEOUT = _safe_int_env("EMAIL_TIMEOUT", 10)
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@sisoc.local")
PWA_WEB_PUSH_PUBLIC_KEY = os.getenv("PWA_WEB_PUSH_PUBLIC_KEY", "").strip()
PWA_WEB_PUSH_PRIVATE_KEY = os.getenv("PWA_WEB_PUSH_PRIVATE_KEY", "").strip()
PWA_WEB_PUSH_SUBJECT = os.getenv(
    "PWA_WEB_PUSH_SUBJECT",
    f"mailto:{DEFAULT_FROM_EMAIL}",
).strip()
PWA_WEB_PUSH_ENABLED = bool(
    PWA_WEB_PUSH_PUBLIC_KEY and PWA_WEB_PUSH_PRIVATE_KEY and PWA_WEB_PUSH_SUBJECT
)

email_backend_errors = []
if EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend":
    raw_port = os.getenv("EMAIL_PORT", "").strip()
    if raw_port:
        try:
            parsed_port = int(raw_port)
            if parsed_port <= 0:
                email_backend_errors.append("EMAIL_PORT debe ser > 0")
        except ValueError:
            email_backend_errors.append("EMAIL_PORT inválido")

    raw_tls = os.getenv("EMAIL_USE_TLS", "").strip().lower()
    raw_ssl = os.getenv("EMAIL_USE_SSL", "").strip().lower()
    valid_bool_values = ("1", "true", "yes", "on", "0", "false", "no", "off")
    if raw_tls and raw_tls not in valid_bool_values:
        email_backend_errors.append("EMAIL_USE_TLS inválido")
    if raw_ssl and raw_ssl not in valid_bool_values:
        email_backend_errors.append("EMAIL_USE_SSL inválido")

    if EMAIL_USE_TLS and EMAIL_USE_SSL:
        email_backend_errors.append("EMAIL_USE_TLS y EMAIL_USE_SSL no pueden ser true")

    if not os.getenv("EMAIL_HOST", "").strip():
        email_backend_errors.append("EMAIL_HOST vacío")
    if not EMAIL_HOST_USER.strip():
        email_backend_errors.append("EMAIL_HOST_USER vacío")
    if not EMAIL_HOST_PASSWORD.strip():
        email_backend_errors.append("EMAIL_HOST_PASSWORD vacío")

if email_backend_errors:
    settings_logger.warning(
        "Configuración SMTP inválida. Se usa backend de consola. Errores: %s",
        "; ".join(email_backend_errors),
    )
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
DB_CONN_MAX_AGE = int(
    os.getenv("DB_CONN_MAX_AGE", "60" if IS_PRODUCTION_LIKE_ENVIRONMENT else "0")
)
DB_CONN_HEALTH_CHECKS = os.getenv(
    "DB_CONN_HEALTH_CHECKS",
    "true" if IS_PRODUCTION_LIKE_ENVIRONMENT else "false",
).strip().lower() in ("1", "true", "yes", "on")

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
        "CONN_MAX_AGE": DB_CONN_MAX_AGE,
        "CONN_HEALTH_CHECKS": DB_CONN_HEALTH_CHECKS,
    }
}

# DB para testing
RUNNING_TESTS = is_running_tests(os.environ, sys.argv)
if RUNNING_TESTS and not SECRET_KEY:
    SECRET_KEY = "test-secret-key"
USE_SQLITE_FOR_TESTS = _safe_bool_env("USE_SQLITE_FOR_TESTS", True)
if RUNNING_TESTS and (USE_SQLITE_FOR_TESTS or not os.environ.get("DATABASE_HOST")):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
            "TEST": {"MIGRATE": False},
        }
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
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# Swagger/OpenAPI
SPECTACULAR_SETTINGS = {
    "TITLE": "SISOC API",
    "DESCRIPTION": "API de gestión de comedores, centros de familia y más",
    "VERSION": "1.0.0",
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": "Usar formato: Api-Key TU_API_KEY",
            }
        }
    },
    "SECURITY": [{"ApiKeyAuth": []}],
    "ENUM_NAME_OVERRIDES": {
        "ActividadCentroEstadoEnum": [
            ("planificada", "Planificada"),
            ("en_curso", "En curso"),
            ("finalizada", "Finalizada"),
        ],
        "ParticipanteActividadEstadoEnum": [
            ("inscrito", "Inscrito"),
            ("lista_espera", "Lista de Espera"),
            ("dado_baja", "Dado de Baja"),
        ],
    },
}

# Dominios / Integraciones
DOMINIO = os.environ.get("DOMINIO", "localhost:8001")
SENTRY_DSN = os.getenv("SENTRY_DSN", "").strip()
SENTRY_LOG_EVENT_LEVEL = "WARNING"
if ENVIRONMENT == "qa":
    SENTRY_ERROR_SAMPLE_RATE = 0.75
    SENTRY_TRACES_SAMPLE_RATE = 0.75
    SENTRY_PROFILES_SAMPLE_RATE = 0.0
    SENTRY_REPLAY_ENABLED = False
    SENTRY_REPLAYS_SESSION_SAMPLE_RATE = 0.0
    SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE = 0.0
elif IS_PRODUCTION_LIKE_ENVIRONMENT:
    SENTRY_ERROR_SAMPLE_RATE = 1.0
    SENTRY_TRACES_SAMPLE_RATE = 1.0
    SENTRY_PROFILES_SAMPLE_RATE = 0.0
    SENTRY_REPLAY_ENABLED = True
    SENTRY_REPLAYS_SESSION_SAMPLE_RATE = 1.0
    SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE = 1.0
else:
    SENTRY_ERROR_SAMPLE_RATE = 0.0
    SENTRY_TRACES_SAMPLE_RATE = 0.0
    SENTRY_PROFILES_SAMPLE_RATE = 0.0
    SENTRY_REPLAY_ENABLED = False
    SENTRY_REPLAYS_SESSION_SAMPLE_RATE = 0.0
    SENTRY_REPLAYS_ON_ERROR_SAMPLE_RATE = 0.0
RENAPER_API_USERNAME = os.getenv("RENAPER_API_USERNAME")
RENAPER_API_PASSWORD = os.getenv("RENAPER_API_PASSWORD")
RENAPER_API_URL = "https://wsv2.secretarianaf.gob.ar/api"
RENAPER_VALIDACION_MAX_RETRIES = _safe_int_env(
    "RENAPER_VALIDACION_MAX_RETRIES",
    1,
)
RENAPER_VALIDACION_BACKOFF_SECONDS = _safe_float_env(
    "RENAPER_VALIDACION_BACKOFF_SECONDS",
    0.0,
)
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

# Changelog
CHANGELOG_GITHUB_URL = (
    "https://raw.githubusercontent.com/dsocial118/BACKOFFICE/main/CHANGELOG.md"
)

# IPs internas
INTERNAL_IPS = ["127.0.0.1", "::1"]

# Logging (asegurar directorio)
LOG_DIR = Path(os.getenv("LOG_DIR", str(BASE_DIR / "logs")))
try:
    os.makedirs(LOG_DIR, exist_ok=True)
except OSError as exc:
    fallback_log_dir = Path(
        os.getenv(
            "LOG_FALLBACK_DIR",
            str(Path(tempfile.gettempdir()) / "sisoc-logs"),
        )
    )
    os.makedirs(fallback_log_dir, exist_ok=True)
    print(
        "[logging] No se pudo crear LOG_DIR="
        f"'{LOG_DIR}' ({exc}). Usando fallback '{fallback_log_dir}'.",
        file=sys.stderr,
    )
    LOG_DIR = fallback_log_dir

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
        "sentry": {
            "level": SENTRY_LOG_EVENT_LEVEL,
            "class": "sentry.handlers.SentryEventHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": [
            "info_file",
            "error_file",
            "warning_file",
            "critical_file",
            "data_file",
            "sentry",
        ],
        "level": "DEBUG" if DEBUG else "INFO",
    },
    "loggers": {
        "django": {
            "handlers": [],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["error_file", "sentry"],
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

# Herramientas debug/perf en desarrollo (desactivadas en tests para estabilidad y velocidad)
if DEBUG and not RUNNING_TESTS:
    INSTALLED_APPS += ["debug_toolbar", "silk"]
    MIDDLEWARE.insert(
        3, "debug_toolbar.middleware.DebugToolbarMiddleware"
    )  # index tras Cors/Common
    MIDDLEWARE += ["silk.middleware.SilkyMiddleware"]
    DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda request: True}
    SILKY_PYTHON_PROFILER = True

# Seguridad por entorno
if IS_PRODUCTION_LIKE_ENVIRONMENT:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
        },
    }
    SECURE_HSTS_SECONDS = 1800  # 30 minutos
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    USE_X_FORWARDED_HOST = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
    ENABLE_CSP = True
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = "SAMEORIGIN"
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
    ENABLE_CSP = True

# Overrides y flags de endurecimiento CSP (migración gradual)
ENABLE_CSP = os.getenv("ENABLE_CSP", str(ENABLE_CSP)).lower() == "true"
CSP_REPORT_ONLY = os.getenv("CSP_REPORT_ONLY", "true").lower() == "true"
# En tests usamos modo enforce por defecto para evitar dependencia del .env local.
if RUNNING_TESTS:
    CSP_REPORT_ONLY = False
CSP_ALLOW_UNSAFE_INLINE_SCRIPTS = (
    os.getenv("CSP_ALLOW_UNSAFE_INLINE_SCRIPTS", "false").lower() == "true"
)
CSP_ALLOW_UNSAFE_EVAL = os.getenv("CSP_ALLOW_UNSAFE_EVAL", "false").lower() == "true"

# Config propia (constantes)
PROG_MILD = 24
PROG_CDIF = 23
PROG_CDLE = 25
PROG_PDV = 26
PROG_MA = 30
PROG_SL = 21

# ============================================================================
# VAT - VOUCHER SYSTEM CONFIGURATION
# ============================================================================

VOUCHER_CONFIG = {
    "ENABLED": True,
    "RECARGA_AUTOMATICA": True,
    "DIA_RECARGA": 1,  # Day of month for automatic reload (1-31)
    "CANTIDAD_RECARGA": 50,  # Credits to reload per voucher
    "PROGRAMA_DEFECTO": "Programa VAT",
    "DIAS_ANTES_VENCIMIENTO_NOTIFICACION": 7,  # Days before expiration to notify
}
