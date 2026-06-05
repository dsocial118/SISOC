from pathlib import Path

from config.settings import *  # noqa: F401,F403

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_URLCONF = "config.urls_preview"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "preview.sqlite3",
    }
}
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]


class _DisableMigrations(dict):
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = _DisableMigrations()

TEMPLATES[0]["DIRS"] = [BASE_DIR / "templates_preview"] + list(TEMPLATES[0]["DIRS"])
