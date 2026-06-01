"""Tests del Req 3 del issue #1799: el Numero de GDE se gestiona desde el Legajo
de la Organizacion (unica fuente) y se replica a las admisiones."""

import json

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from admisiones.models.admisiones import (
    Admision,
    ArchivoAdmision,
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
from organizaciones.views import actualizar_numero_gde_documento_organizacion


pytestmark = pytest.mark.django_db
User = get_user_model()


@pytest.fixture
def superuser():
    return User.objects.create_superuser(username="su_gde_org", password="pwd")


@pytest.fixture
def setup():
    tipo = TipoEntidad.objects.create(nombre="Personería Jurídica")
    organizacion = Organizacion.objects.create(nombre="Org GDE", tipo_entidad=tipo)
    comedor = Comedor.objects.create(nombre="Comedor GDE", organizacion=organizacion)
    EstadoAdmision.objects.create(pk=1, nombre="Pendiente")
    EstadoAdmision.objects.create(pk=2, nombre="Doc en proceso")
    tipo_convenio = TipoConvenio.objects.create(pk=3, nombre="Personería Jurídica")
    admision = Admision.objects.create(
        comedor=comedor,
        tipo_convenio=tipo_convenio,
        tipo_entidad_origen=tipo,
        estado_admision="documentacion_en_proceso",
    )
    doc_org = DocumentacionOrganizacion.objects.create(
        nombre="DNI del Presidente",
        categoria=DocumentacionOrganizacion.CATEGORIA_PERSONERIA,
        obligatorio=True,
    )
    archivo_org = ArchivoOrganizacion.objects.create(
        organizacion=organizacion,
        documentacion=doc_org,
        archivo="organizaciones/documentacion/dni.pdf",
        estado=ArchivoOrganizacion.ESTADO_ACEPTADO,
    )
    archivo_adm = ArchivoAdmision.objects.create(
        admision=admision,
        documentacion=None,
        nombre_personalizado="DNI del Presidente",
        archivo="organizaciones/documentacion/dni.pdf",
        estado="Aceptado",
        archivo_organizacion_origen=archivo_org,
    )
    return {
        "organizacion": organizacion,
        "admision": admision,
        "archivo_org": archivo_org,
        "archivo_adm": archivo_adm,
    }


def _post_gde(user, archivo_id, numero_gde):
    request = RequestFactory().post(
        f"/organizaciones/documentacion/{archivo_id}/numero-gde/",
        data={"numero_gde": numero_gde},
    )
    request.user = user
    return actualizar_numero_gde_documento_organizacion(request, archivo_id)


def test_gde_en_legajo_se_replica_a_admisiones(setup, superuser):
    response = _post_gde(superuser, setup["archivo_org"].id, "GDE-2026-0001")
    assert response.status_code == 200
    data = json.loads(response.content)
    assert data["success"] is True

    setup["archivo_org"].refresh_from_db()
    setup["archivo_adm"].refresh_from_db()
    assert setup["archivo_org"].numero_gde == "GDE-2026-0001"
    # Replicado al ArchivoAdmision materializado.
    assert setup["archivo_adm"].numero_gde == "GDE-2026-0001"


def test_gde_rechaza_documento_no_aceptado(setup, superuser):
    setup["archivo_org"].estado = ArchivoOrganizacion.ESTADO_A_VALIDAR
    setup["archivo_org"].save(update_fields=["estado"])

    response = _post_gde(superuser, setup["archivo_org"].id, "GDE-X")
    assert response.status_code == 400
    setup["archivo_org"].refresh_from_db()
    assert setup["archivo_org"].numero_gde is None


def test_replicacion_no_toca_admisiones_archivadas(setup, superuser):
    setup["admision"].enviada_a_archivo = True
    setup["admision"].save(update_fields=["enviada_a_archivo"])

    actualizados = AdmisionService.replicar_numero_gde_desde_organizacion(
        _con_gde(setup["archivo_org"], "GDE-NUEVO"), superuser
    )
    assert actualizados == 0
    setup["archivo_adm"].refresh_from_db()
    assert setup["archivo_adm"].numero_gde != "GDE-NUEVO"


def test_admision_no_puede_editar_gde_de_doc_organizacional(setup, superuser):
    """El endpoint admision-side rechaza editar el GDE de un documento de origen
    organizacional (se gestiona desde el legajo)."""
    request = RequestFactory().post(
        "/ajax/actualizar-numero-gde/",
        data={"documento_id": setup["archivo_adm"].id, "numero_gde": "GDE-HACK"},
    )
    request.user = superuser
    resultado = AdmisionService.actualizar_numero_gde_ajax(request)
    assert resultado["success"] is False
    assert "legajo de la organización" in resultado["error"].lower()


def _con_gde(archivo_org, numero):
    archivo_org.numero_gde = numero
    archivo_org.save(update_fields=["numero_gde"])
    return archivo_org
