"""Issue #1799 (feedback punto 4): al cambiar el estado de un documento via AJAX,
la celda "Número de GDE" se re-renderiza para que el campo aparezca/oculte sin
recargar. Antes, aceptar un documento nativo de la Admisión dejaba la celda con el
"-" del render previo (Pendiente). Tests del re-render server-side de la celda."""

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from admisiones.models.admisiones import (
    Admision,
    ArchivoAdmision,
    Documentacion,
    EstadoAdmision,
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
User = get_user_model()


@pytest.fixture
def setup():
    tipo = TipoEntidad.objects.create(nombre="Personería Jurídica")
    organizacion = Organizacion.objects.create(nombre="Org GDE", tipo_entidad=tipo)
    comedor = Comedor.objects.create(nombre="Comedor GDE", organizacion=organizacion)
    EstadoAdmision.objects.create(pk=1, nombre="Pendiente")
    tipo_convenio = TipoConvenio.objects.create(pk=3, nombre="Personería Jurídica")
    admision = Admision.objects.create(
        comedor=comedor,
        tipo_convenio=tipo_convenio,
        tipo_entidad_origen=tipo,
        estado_admision="documentacion_en_proceso",
    )
    documentacion = Documentacion.objects.create(
        nombre="Nota de Solicitud e Inclusión al Programa", obligatorio=True
    )
    return {
        "organizacion": organizacion,
        "admision": admision,
        "documentacion": documentacion,
    }


def _request(user):
    request = RequestFactory().post("/ajax/actualizar-estado-archivo/")
    request.user = user
    return request


def test_doc_nativo_aceptado_devuelve_campo_gde_editable(setup):
    """Un documento NATIVO de la admisión aceptado debe exponer el campo GDE
    editable (no un '-'), que es justo lo que faltaba al aceptar via AJAX."""
    superuser = User.objects.create_superuser(username="su", password="pwd")
    archivo = ArchivoAdmision.objects.create(
        admision=setup["admision"],
        documentacion=setup["documentacion"],
        archivo="admisiones/nota.pdf",
        estado="aceptado",
    )

    resultado = AdmisionService._build_success_actualizar_estado_ajax_response(
        archivo=archivo,
        display_objetivo="Aceptado",
        grupo_usuario="Abogado Dupla",
        request=_request(superuser),
    )

    html = resultado["gde_html"]
    # Widget GDE editable presente (vista + edición): esto es lo que faltaba.
    assert f"gde-display-{archivo.id}" in html
    assert f"gde-input-{archivo.id}" in html
    assert "Sin número GDE" in html


def test_doc_origen_organizacion_aceptado_es_solo_lectura(setup):
    """Un documento de origen organizacional sigue siendo solo lectura admisión-side
    (el GDE se gestiona desde el Legajo, #1799 Req 3): sin input de edición."""
    superuser = User.objects.create_superuser(username="su2", password="pwd")
    doc_org = DocumentacionOrganizacion.objects.create(
        nombre="DNI del Presidente",
        categoria=DocumentacionOrganizacion.CATEGORIA_PERSONERIA,
        obligatorio=True,
    )
    archivo_org = ArchivoOrganizacion.objects.create(
        organizacion=setup["organizacion"],
        documentacion=doc_org,
        archivo="organizaciones/dni.pdf",
        estado=ArchivoOrganizacion.ESTADO_ACEPTADO,
    )
    archivo = ArchivoAdmision.objects.create(
        admision=setup["admision"],
        documentacion=setup["documentacion"],
        archivo="admisiones/dni.pdf",
        estado="aceptado",
        archivo_organizacion_origen=archivo_org,
    )

    html = AdmisionService._render_celda_gde_html(archivo, _request(superuser))

    assert f"gde-input-{archivo.id}" not in html
    assert "bi-info-circle" in html
    assert "Sin número GDE" in html


def test_doc_no_aceptado_no_muestra_campo_gde(setup):
    """Un documento no aceptado muestra '-' (sin campo GDE)."""
    superuser = User.objects.create_superuser(username="su3", password="pwd")
    archivo = ArchivoAdmision.objects.create(
        admision=setup["admision"],
        documentacion=setup["documentacion"],
        archivo="admisiones/nota.pdf",
        estado="pendiente",
    )

    html = AdmisionService._render_celda_gde_html(archivo, _request(superuser))

    # Ni editable ni solo-lectura-org: cae en la rama del guion "-".
    assert f"gde-display-{archivo.id}" not in html
    assert "Sin número GDE" not in html
    assert "bi-info-circle" not in html


def test_render_celda_gde_sin_request_devuelve_none(setup):
    archivo = ArchivoAdmision.objects.create(
        admision=setup["admision"],
        documentacion=setup["documentacion"],
        archivo="admisiones/nota.pdf",
        estado="aceptado",
    )
    assert AdmisionService._render_celda_gde_html(archivo, None) is None
