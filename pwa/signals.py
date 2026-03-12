from django.db.utils import ProgrammingError, OperationalError

from pwa.catalogo_seed import bootstrap_catalogo_actividades


def seed_catalogo_actividades(sender, **kwargs):
    try:
        bootstrap_catalogo_actividades(using=kwargs.get("using", "default"))
    except (ProgrammingError, OperationalError):
        # La tabla aún no existe (DB nueva antes de que corran las migraciones de pwa).
        pass
