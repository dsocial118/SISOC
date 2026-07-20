import importlib

import pytest
from django.apps import apps as global_apps

from admisiones.models.admisiones import (
    Admision,
    ArchivoAdmision,
    Documentacion,
    TipoConvenio,
)
from comedores.models import Comedor
from organizaciones.models import (
    ArchivoOrganizacion,
    DocumentacionOrganizacion,
    Organizacion,
)


pytestmark = pytest.mark.django_db


_migracion = importlib.import_module(
    "organizaciones.migrations.0016_issue_2083_documentacion_organizacion"
)


def _crear_archivo_arca(tipo_convenio, categoria, sufijo):
    organizacion = Organizacion.objects.create(nombre=f"Organizacion {sufijo}")
    comedor = Comedor.objects.create(
        nombre=f"Comedor {sufijo}", organizacion=organizacion
    )
    admision = Admision.objects.create(comedor=comedor, tipo_convenio=tipo_convenio)
    documentacion = DocumentacionOrganizacion.objects.create(
        nombre=_migracion.ARCA_NOMBRE,
        categoria=categoria,
    )
    archivo = ArchivoOrganizacion.objects.create(
        organizacion=organizacion,
        documentacion=documentacion,
        archivo=f"organizaciones/documentacion/arca-{sufijo}.pdf",
        estado=ArchivoOrganizacion.ESTADO_ACEPTADO,
    )
    return admision, archivo


def test_migracion_materializa_arca_en_documento_del_tipo_convenio():
    convenio_juridico = TipoConvenio.objects.create(nombre="Personeria Juridica")
    convenio_eclesiastico = TipoConvenio.objects.create(
        nombre="Personeria Juridica Eclesiastica"
    )
    documento_juridico = Documentacion.objects.create(
        nombre="Constancia de ARCA", obligatorio=True, orden=10
    )
    documento_juridico.convenios.add(convenio_juridico)
    documento_eclesiastico = Documentacion.objects.create(
        nombre="Constancia de ARCA", obligatorio=True, orden=5
    )
    documento_eclesiastico.convenios.add(convenio_eclesiastico)
    admision_juridica, archivo_juridico = _crear_archivo_arca(
        convenio_juridico,
        DocumentacionOrganizacion.CATEGORIA_PERSONERIA,
        "juridico",
    )
    admision_eclesiastica, archivo_eclesiastico = _crear_archivo_arca(
        convenio_eclesiastico,
        DocumentacionOrganizacion.CATEGORIA_ECLESIASTICA,
        "eclesiastico",
    )

    _migracion.actualizar_documentacion(global_apps, None)

    archivos_admision = {
        archivo.admision_id: archivo
        for archivo in ArchivoAdmision.objects.filter(
            archivo_organizacion_origen_id__in=[
                archivo_juridico.id,
                archivo_eclesiastico.id,
            ]
        )
    }
    assert (
        archivos_admision[admision_juridica.id].documentacion_id
        == documento_juridico.id
    )
    assert (
        archivos_admision[admision_eclesiastica.id].documentacion_id
        == documento_eclesiastico.id
    )
    assert (
        ArchivoOrganizacion.all_objects.filter(
            id__in=[archivo_juridico.id, archivo_eclesiastico.id],
            deleted_at__isnull=False,
        ).count()
        == 2
    )
