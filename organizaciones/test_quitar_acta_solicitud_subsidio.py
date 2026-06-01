"""Tests del Req 2 del issue #1799: el "Acta de solicitud de subsidio al
programa" se quita del legajo de la Organizacion (vuelve a la Admision)."""

import importlib

import pytest
from django.apps import apps as global_apps

from admisiones.services.admisiones_service.impl import AdmisionService
from organizaciones.models import (
    ArchivoOrganizacion,
    DocumentacionOrganizacion,
    Organizacion,
    TipoEntidad,
)


pytestmark = pytest.mark.django_db

_migracion = importlib.import_module(
    "organizaciones.migrations.0015_quitar_acta_solicitud_subsidio"
)
quitar_acta_del_legajo = _migracion.quitar_acta_del_legajo
ACTA_NOMBRE = _migracion.ACTA_NOMBRE


def test_migracion_quita_acta_del_catalogo_y_soft_deletea_archivos():
    tipo = TipoEntidad.objects.create(nombre="Personería Jurídica")
    organizacion = Organizacion.objects.create(nombre="Org Acta", tipo_entidad=tipo)
    acta_doc = DocumentacionOrganizacion.objects.create(
        nombre=ACTA_NOMBRE,
        categoria=DocumentacionOrganizacion.CATEGORIA_PERSONERIA,
        obligatorio=True,
    )
    archivo = ArchivoOrganizacion.objects.create(
        organizacion=organizacion,
        documentacion=acta_doc,
        archivo="organizaciones/documentacion/acta.pdf",
        estado=ArchivoOrganizacion.ESTADO_ACEPTADO,
    )

    quitar_acta_del_legajo(global_apps, None)

    # El acta ya no esta en el catalogo del legajo.
    assert not DocumentacionOrganizacion.objects.filter(nombre=ACTA_NOMBRE).exists()
    # El archivo cargado fue soft-deleteado (no se borra fisicamente).
    assert not ArchivoOrganizacion.objects.filter(pk=archivo.pk).exists()
    assert ArchivoOrganizacion.all_objects.filter(
        pk=archivo.pk, deleted_at__isnull=False
    ).exists()


def test_migracion_es_idempotente_sin_acta():
    # Sin acta cargada no debe fallar.
    quitar_acta_del_legajo(global_apps, None)
    assert not DocumentacionOrganizacion.objects.filter(nombre=ACTA_NOMBRE).exists()


def test_alias_organizacional_ya_no_mapea_el_acta():
    alias_personeria = AdmisionService.ALIAS_DOCUMENTACION_ORGANIZACIONAL[
        DocumentacionOrganizacion.CATEGORIA_PERSONERIA
    ]
    assert "acta de solicitud de subsidio" not in alias_personeria
