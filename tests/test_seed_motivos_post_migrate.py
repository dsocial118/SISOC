"""Regresion: el seed post_migrate del catalogo de motivos no debe romper un
``migrate`` parcial cuando su tabla todavia no existe.

El entrypoint de produccion corre ``migrate auth`` antes del ``migrate``
general. Django emite ``post_migrate`` para todas las apps en cada invocacion,
asi que el receptor se ejecuta con relevamientos todavia en 0013 (sin la tabla
del catalogo). Sin el guard, ``get_or_create`` lanzaba ProgrammingError 1146 y
el contenedor entraba en crash-loop antes de aplicar 0014..0017.
"""

import pytest
from django.apps import apps
from django.db import connection

from relevamientos.models import MotivoExcepcionSeguimiento
from relevamientos.signals import sembrar_motivos_excepcion_seguimiento

SENDER = apps.get_app_config("relevamientos")


@pytest.mark.django_db
def test_seed_no_toca_la_base_si_la_tabla_del_catalogo_no_existe(mocker):
    """Simula el ``migrate auth`` inicial de prod: la tabla aun no fue creada."""
    tabla = MotivoExcepcionSeguimiento._meta.db_table
    sin_tabla = [t for t in connection.introspection.table_names() if t != tabla]
    mocker.patch.object(connection.introspection, "table_names", return_value=sin_tabla)
    get_or_create = mocker.patch.object(
        MotivoExcepcionSeguimiento.objects, "get_or_create"
    )

    # No debe lanzar ni intentar consultar una tabla inexistente.
    sembrar_motivos_excepcion_seguimiento(SENDER, using="default")

    get_or_create.assert_not_called()


@pytest.mark.django_db
def test_seed_siembra_los_motivos_canonicos_cuando_la_tabla_existe():
    MotivoExcepcionSeguimiento.objects.all().delete()

    sembrar_motivos_excepcion_seguimiento(SENDER, using="default")

    assert set(
        MotivoExcepcionSeguimiento.objects.values_list("nombre", flat=True)
    ) == set(MotivoExcepcionSeguimiento.MOTIVOS_CANONICOS)


@pytest.mark.django_db
def test_seed_es_idempotente():
    sembrar_motivos_excepcion_seguimiento(SENDER, using="default")
    sembrar_motivos_excepcion_seguimiento(SENDER, using="default")

    assert MotivoExcepcionSeguimiento.objects.count() == len(
        MotivoExcepcionSeguimiento.MOTIVOS_CANONICOS
    )


@pytest.mark.django_db
def test_seed_ignora_otras_apps():
    """El receptor se dispara para todas las apps; solo actua para relevamientos."""
    MotivoExcepcionSeguimiento.objects.all().delete()

    sembrar_motivos_excepcion_seguimiento(apps.get_app_config("auth"), using="default")

    assert not MotivoExcepcionSeguimiento.objects.exists()
