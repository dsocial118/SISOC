"""Regresiones de la separacion de documentos en una admision.

Una admision muestra documentos del legajo de la organizacion, documentos
propios definidos por el convenio y documentos adicionales opcionales. Los
primeros no deben reaparecer como adicionales cuando fueron materializados sin
un ``Documentacion`` equivalente.
"""

import pytest

from admisiones.models.admisiones import (
    Admision,
    ArchivoAdmision,
    Documentacion,
    TipoConvenio,
)
from admisiones.services.admisiones_service import AdmisionService
from comedores.models import Comedor
from organizaciones.models import (
    ArchivoOrganizacion,
    DocumentacionOrganizacion,
    Organizacion,
    TipoEntidad,
)


pytestmark = pytest.mark.django_db


def test_contexto_separa_documentos_organizacionales_propios_y_adicionales():
    tipo_entidad = TipoEntidad.objects.create(nombre="Personeria Juridica")
    organizacion = Organizacion.objects.create(
        nombre="Organizacion documentos", tipo_entidad=tipo_entidad
    )
    comedor = Comedor.objects.create(
        nombre="Comedor documentos", organizacion=organizacion
    )
    convenio = TipoConvenio.objects.create(pk=3, nombre="Personeria Juridica")
    admision = Admision.objects.create(
        comedor=comedor,
        tipo_convenio=convenio,
        tipo_entidad_origen=tipo_entidad,
        estado_admision="documentacion_en_proceso",
    )

    documento_organizacion = DocumentacionOrganizacion.objects.create(
        nombre="Documento institucional sin equivalente",
        categoria=DocumentacionOrganizacion.CATEGORIA_PERSONERIA,
        obligatorio=True,
    )
    archivo_organizacion = ArchivoOrganizacion.objects.create(
        organizacion=organizacion,
        documentacion=documento_organizacion,
        archivo="organizaciones/documento-institucional.pdf",
        estado=ArchivoOrganizacion.ESTADO_ACEPTADO,
    )
    ArchivoAdmision.objects.create(
        admision=admision,
        nombre_personalizado=documento_organizacion.nombre,
        archivo="admisiones/documento-institucional.pdf",
        estado="Aceptado",
        archivo_organizacion_origen=archivo_organizacion,
    )
    ArchivoAdmision.objects.create(
        admision=admision,
        nombre_personalizado=documento_organizacion.nombre,
        archivo="admisiones/documento-institucional-legacy.pdf",
        estado="Aceptado",
    )

    documento_propio = Documentacion.objects.create(
        nombre="Acta de solicitud de subsidio", obligatorio=True
    )
    documento_propio.convenios.add(convenio)
    ArchivoAdmision.objects.create(
        admision=admision,
        documentacion=documento_propio,
        archivo="admisiones/acta-solicitud.pdf",
        estado="Documento adjunto",
    )

    ArchivoAdmision.objects.create(
        admision=admision,
        nombre_personalizado="Nota complementaria",
        archivo="admisiones/nota-complementaria.pdf",
        estado="Documento adjunto",
    )
    adicional_legajo = ArchivoOrganizacion.objects.create(
        organizacion=organizacion,
        nombre_personalizado="Nota adicional del legajo",
        archivo="organizaciones/nota-adicional.pdf",
        estado=ArchivoOrganizacion.ESTADO_ACEPTADO,
    )
    ArchivoAdmision.objects.create(
        admision=admision,
        nombre_personalizado=adicional_legajo.nombre_personalizado,
        archivo="admisiones/nota-adicional.pdf",
        estado="Aceptado",
        archivo_organizacion_origen=adicional_legajo,
    )

    contexto = AdmisionService.get_admision_update_context(admision)

    assert {documento["nombre"] for documento in contexto["documentos"]} == {
        "Documento institucional sin equivalente",
        "Acta de solicitud de subsidio",
    }
    assert {
        documento["nombre"] for documento in contexto["documentos_personalizados"]
    } == {"Nota complementaria", "Nota adicional del legajo"}
