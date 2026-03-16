from django.db import connections

from pwa.catalogo_seed import bootstrap_catalogo_actividades
from pwa.models import CatalogoActividadPWA


def seed_catalogo_actividades(sender, **kwargs):
    using = kwargs.get("using", "default")
    connection = connections[using]
    table_name = CatalogoActividadPWA._meta.db_table

    if table_name not in connection.introspection.table_names():
        return

    bootstrap_catalogo_actividades(using=using)
