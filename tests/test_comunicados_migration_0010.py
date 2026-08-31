from importlib import import_module

import pytest
from django.apps import apps
from django.contrib.auth.models import User

from comunicados.models import Comunicado


MIGRATION = import_module("comunicados.migrations.0010_archive_importacion_nomina")
CORRECTIVE_MIGRATION = import_module(
    "comunicados.migrations.0011_rearchive_importacion_nomina"
)
PREFIX_CORRECTIVE_MIGRATION = import_module(
    "comunicados.migrations.0012_rearchive_importacion_nomina_with_prefix"
)


@pytest.mark.django_db
def test_migracion_archiva_solo_comunicados_internos_publicados_del_titulo():
    creador = User.objects.create_user(username="comunicados-issue-2304")
    objetivo = Comunicado.objects.create(
        titulo="Importación de nómina (resultado del proceso)",
        cuerpo="Contenido obsoleto",
        estado="publicado",
        destacado=True,
        tipo="interno",
        usuario_creador=creador,
    )
    ya_archivado = Comunicado.objects.create(
        titulo="Importación de nómina (histórico)",
        cuerpo="Contenido histórico",
        estado="archivado",
        destacado=True,
        tipo="interno",
        usuario_creador=creador,
    )
    externo = Comunicado.objects.create(
        titulo="Importación de nómina (externo)",
        cuerpo="Contenido externo",
        estado="publicado",
        destacado=True,
        tipo="externo",
        usuario_creador=creador,
    )
    no_coincidente = Comunicado.objects.create(
        titulo="Otro comunicado",
        cuerpo="Contenido vigente",
        estado="publicado",
        destacado=True,
        tipo="interno",
        usuario_creador=creador,
    )

    MIGRATION.archivar_comunicados_importacion_nomina(apps, None)

    objetivo.refresh_from_db()
    ya_archivado.refresh_from_db()
    externo.refresh_from_db()
    no_coincidente.refresh_from_db()
    assert objetivo.estado == "archivado"
    assert objetivo.destacado is False
    assert ya_archivado.estado == "archivado"
    assert ya_archivado.destacado is True
    assert externo.estado == "publicado"
    assert externo.destacado is True
    assert no_coincidente.estado == "publicado"
    assert no_coincidente.destacado is True


@pytest.mark.django_db
def test_migracion_correctiva_archiva_objetivo_creado_despues_de_0010():
    creador = User.objects.create_user(username="comunicados-correctivo")
    objetivo = Comunicado.objects.create(
        titulo="Importación de nómina (resultado del proceso)",
        cuerpo="Contenido creado después de la migración original",
        estado="publicado",
        destacado=True,
        tipo="interno",
        usuario_creador=creador,
    )

    CORRECTIVE_MIGRATION.archivar_comunicado_importacion_nomina(apps, None)

    objetivo.refresh_from_db()
    assert objetivo.estado == "archivado"
    assert objetivo.destacado is False


@pytest.mark.django_db
def test_migracion_correctiva_archiva_objetivo_con_emoji_inicial():
    creador = User.objects.create_user(username="comunicados-correctivo-emoji")
    objetivo = Comunicado.objects.create(
        titulo="📋 Importación de nómina en nuevas admisiones",
        cuerpo="Contenido obsoleto publicado en HML",
        estado="publicado",
        destacado=True,
        tipo="interno",
        usuario_creador=creador,
    )
    externo = Comunicado.objects.create(
        titulo="📋 Importación de nómina para destinatarios externos",
        cuerpo="Contenido externo vigente",
        estado="publicado",
        destacado=True,
        tipo="externo",
        usuario_creador=creador,
    )
    no_coincidente = Comunicado.objects.create(
        titulo="📋 Nueva funcionalidad de admisiones",
        cuerpo="Contenido interno vigente",
        estado="publicado",
        destacado=True,
        tipo="interno",
        usuario_creador=creador,
    )

    PREFIX_CORRECTIVE_MIGRATION.archivar_comunicado_importacion_nomina_con_prefijo(
        apps, None
    )

    objetivo.refresh_from_db()
    externo.refresh_from_db()
    no_coincidente.refresh_from_db()
    assert objetivo.estado == "archivado"
    assert objetivo.destacado is False
    assert externo.estado == "publicado"
    assert externo.destacado is True
    assert no_coincidente.estado == "publicado"
    assert no_coincidente.destacado is True
