import importlib
from types import SimpleNamespace

from django.apps import apps as global_apps
from django.db import DEFAULT_DB_ALIAS

from core.models import Municipio, Provincia
from pas.api import ResumenTitularPAS, obtener_resumen_titular
from pas.models import PasAviso, PasEstado, PasPersona


_migration = importlib.import_module("pas.migrations.0001_initial")


def _schema_editor_for_default_database():
    return SimpleNamespace(
        connection=SimpleNamespace(alias=DEFAULT_DB_ALIAS),
    )


def test_obtener_resumen_titular_devuelve_dto_sin_modelos(db):
    estado = PasEstado.objects.create(nombre="Activo")
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    persona = PasPersona.objects.create(
        id_persona=501,
        apellidos="Pérez",
        nombres="Ana",
        dni=30111222,
        provincia=provincia,
        municipio=municipio,
        estado=estado,
    )

    resultado = obtener_resumen_titular(persona.pk)

    assert isinstance(resultado, ResumenTitularPAS)
    assert resultado.persona_id == persona.pk
    assert resultado.id_persona == 501
    assert resultado.estado == "Activo"


def test_obtener_resumen_titular_inexistente_devuelve_none(db):
    assert obtener_resumen_titular(999_999) is None


def test_migracion_inicial_siembra_catalogo_basico_pas(db):
    _migration.cargar_catalogo_pas(
        global_apps,
        _schema_editor_for_default_database(),
    )

    assert set(PasEstado.objects.values_list("nombre", flat=True)) == {
        "Activo",
        "Suspendido",
        "Baja",
    }

    estados_por_aviso = {
        aviso.codigo: set(aviso.estados.values_list("nombre", flat=True))
        for aviso in PasAviso.objects.filter(codigo__in=[1, 10, 55])
    }

    assert estados_por_aviso == {
        1: {"Activo"},
        10: {"Suspendido", "Baja"},
        55: {"Baja"},
    }
