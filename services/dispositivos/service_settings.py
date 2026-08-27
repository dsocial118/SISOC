"""Configuración mínima del ejecutable independiente de Dispositivos.

No recibe tráfico hasta contar con un proveedor JWS y adaptadores de integración.
"""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
SECRET_KEY = os.environ.get("DISPOSITIVOS_SECRET_KEY", "service-check-only-secret")
DEBUG = False
ALLOWED_HOSTS = []
ROOT_URLCONF = "services.dispositivos.service_urls"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "services.dispositivos.shared_catalog.apps.SharedCatalogConfig",
    "services.dispositivos.dispositivos.apps.DispositivosConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    }
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "service.sqlite3",
    }
}
STATIC_URL = "/static/"

# El corte físico preserva las FKs legacy; aún no expone un escritor propio.
DISPOSITIVOS_REQUIRED_PERMISSIONS = "services.dispositivos.service_adapters.permisos_requeridos"
DISPOSITIVOS_REGISTER_FAVORITES = False
