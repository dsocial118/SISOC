"""Tests para el flujo de Numero GDE de archivos de organizacion vistos desde
una Admision (Seccion 3 del issue #1605)."""

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from admisiones.models.admisiones import (
    Admision,
    EstadoAdmision,
    NumeroGdeOrganizacion,
    TipoConvenio,
)
from admisiones.services.admisiones_service import AdmisionService
from comedores.models import Comedor
from duplas.models import Dupla
from organizaciones.models import (
    ArchivoOrganizacion,
    DocumentacionOrganizacion,
    Organizacion,
    TipoEntidad,
)


pytestmark = pytest.mark.django_db
User = get_user_model()


@pytest.fixture
def tecnico():
    return User.objects.create_user(username="tecnico_gde", password="pwd")


@pytest.fixture
def abogado():
    return User.objects.create_user(username="abogado_gde", password="pwd")


@pytest.fixture
def superuser():
    return User.objects.create_superuser(username="su_gde", password="pwd")


@pytest.fixture
def setup_org(tecnico, abogado):
    tipo = TipoEntidad.objects.create(nombre="Personería Jurídica")
    dupla = Dupla.objects.create(
        nombre="Dupla GDE", estado="Activo", abogado=abogado
    )
    dupla.tecnico.add(tecnico)
    organizacion = Organizacion.objects.create(
        nombre="Org GDE", tipo_entidad=tipo
    )
    comedor = Comedor.objects.create(
        nombre="Comedor GDE", organizacion=organizacion, dupla=dupla
    )
    EstadoAdmision.objects.create(nombre="Pendiente")
    tipo_convenio = TipoConvenio.objects.create(pk=3, nombre="Personería Jurídica")
    admision = Admision.objects.create(
        comedor=comedor,
        tipo_convenio=tipo_convenio,
        tipo_entidad_origen=tipo,
        estado_admision="documentacion_en_proceso",
    )
    documentacion_org = DocumentacionOrganizacion.objects.create(
        nombre="DNI Presidente",
        categoria=DocumentacionOrganizacion.CATEGORIA_PERSONERIA,
        obligatorio=True,
    )
    archivo_org = ArchivoOrganizacion.objects.create(
        organizacion=organizacion,
        documentacion=documentacion_org,
        archivo="organizaciones/test-doc.pdf",
        estado=ArchivoOrganizacion.ESTADO_ACEPTADO,
    )
    return {
        "admision": admision,
        "archivo_org": archivo_org,
        "tipo_entidad": tipo,
        "documentacion_org": documentacion_org,
    }


def _build_request(user, data):
    request = RequestFactory().post(
        "/ajax/actualizar-numero-gde-organizacion/", data=data
    )
    request.user = user
    return request


def test_actualizar_numero_gde_organizacion_crea_registro(setup_org, superuser):
    request = _build_request(
        superuser,
        {
            "admision_id": setup_org["admision"].pk,
            "archivo_organizacion_id": setup_org["archivo_org"].pk,
            "numero_gde": "GDE-2026-000001",
        },
    )

    resultado = AdmisionService.actualizar_numero_gde_organizacion_ajax(request)

    assert resultado["success"] is True
    assert resultado["numero_gde"] == "GDE-2026-000001"
    assert resultado["valor_anterior"] is None
    registro = NumeroGdeOrganizacion.objects.get(
        admision=setup_org["admision"],
        archivo_organizacion=setup_org["archivo_org"],
    )
    assert registro.numero_gde == "GDE-2026-000001"
    assert registro.modificado_por_id == superuser.id


def test_actualizar_numero_gde_organizacion_actualiza_existente(
    setup_org, superuser
):
    NumeroGdeOrganizacion.objects.create(
        admision=setup_org["admision"],
        archivo_organizacion=setup_org["archivo_org"],
        numero_gde="GDE-PREVIO",
    )

    request = _build_request(
        superuser,
        {
            "admision_id": setup_org["admision"].pk,
            "archivo_organizacion_id": setup_org["archivo_org"].pk,
            "numero_gde": "GDE-NUEVO",
        },
    )
    resultado = AdmisionService.actualizar_numero_gde_organizacion_ajax(request)

    assert resultado["success"] is True
    assert resultado["valor_anterior"] == "GDE-PREVIO"
    assert resultado["numero_gde"] == "GDE-NUEVO"
    assert NumeroGdeOrganizacion.objects.count() == 1


def test_actualizar_numero_gde_organizacion_rechaza_no_aceptado(
    setup_org, superuser
):
    setup_org["archivo_org"].estado = ArchivoOrganizacion.ESTADO_A_VALIDAR
    setup_org["archivo_org"].save(update_fields=["estado"])

    request = _build_request(
        superuser,
        {
            "admision_id": setup_org["admision"].pk,
            "archivo_organizacion_id": setup_org["archivo_org"].pk,
            "numero_gde": "GDE-X",
        },
    )
    resultado = AdmisionService.actualizar_numero_gde_organizacion_ajax(request)

    assert resultado["success"] is False
    assert "aceptados" in resultado["error"].lower()
    assert NumeroGdeOrganizacion.objects.count() == 0


def test_actualizar_numero_gde_organizacion_rechaza_archivo_de_otra_org(
    setup_org, superuser
):
    otra_org = Organizacion.objects.create(
        nombre="Otra Org", tipo_entidad=setup_org["tipo_entidad"]
    )
    archivo_otra = ArchivoOrganizacion.objects.create(
        organizacion=otra_org,
        documentacion=setup_org["documentacion_org"],
        archivo="organizaciones/otra-doc.pdf",
        estado=ArchivoOrganizacion.ESTADO_ACEPTADO,
    )

    request = _build_request(
        superuser,
        {
            "admision_id": setup_org["admision"].pk,
            "archivo_organizacion_id": archivo_otra.pk,
            "numero_gde": "GDE-Y",
        },
    )
    resultado = AdmisionService.actualizar_numero_gde_organizacion_ajax(request)

    assert resultado["success"] is False
    assert "organizacion" in resultado["error"].lower()


def test_actualizar_numero_gde_organizacion_rechaza_usuario_sin_permisos(
    setup_org,
):
    extranio = User.objects.create_user(username="extranio", password="pwd")
    request = _build_request(
        extranio,
        {
            "admision_id": setup_org["admision"].pk,
            "archivo_organizacion_id": setup_org["archivo_org"].pk,
            "numero_gde": "GDE-Z",
        },
    )
    resultado = AdmisionService.actualizar_numero_gde_organizacion_ajax(request)

    assert resultado["success"] is False
    assert "permisos" in resultado["error"].lower()


def test_misma_organizacion_dos_admisiones_no_comparten_gde(setup_org, superuser):
    """3.3 — el GDE es por admision, aunque el doc-org sea el mismo."""

    # Crear segunda admision sobre el mismo comedor/organizacion
    otra_admision = Admision.objects.create(
        comedor=setup_org["admision"].comedor,
        tipo_convenio=setup_org["admision"].tipo_convenio,
        tipo_entidad_origen=setup_org["tipo_entidad"],
        estado_admision="documentacion_en_proceso",
    )

    AdmisionService.actualizar_numero_gde_organizacion_ajax(
        _build_request(
            superuser,
            {
                "admision_id": setup_org["admision"].pk,
                "archivo_organizacion_id": setup_org["archivo_org"].pk,
                "numero_gde": "GDE-ADM-1",
            },
        )
    )
    AdmisionService.actualizar_numero_gde_organizacion_ajax(
        _build_request(
            superuser,
            {
                "admision_id": otra_admision.pk,
                "archivo_organizacion_id": setup_org["archivo_org"].pk,
                "numero_gde": "GDE-ADM-2",
            },
        )
    )

    registros = {
        reg.admision_id: reg.numero_gde
        for reg in NumeroGdeOrganizacion.objects.filter(
            archivo_organizacion=setup_org["archivo_org"]
        )
    }
    assert registros[setup_org["admision"].pk] == "GDE-ADM-1"
    assert registros[otra_admision.pk] == "GDE-ADM-2"


def test_numero_gde_organizacion_unique_admision_archivo(setup_org):
    """El constraint unique evita duplicados por admision + archivo_organizacion."""

    NumeroGdeOrganizacion.objects.create(
        admision=setup_org["admision"],
        archivo_organizacion=setup_org["archivo_org"],
        numero_gde="A",
    )
    with pytest.raises(Exception):
        NumeroGdeOrganizacion.objects.create(
            admision=setup_org["admision"],
            archivo_organizacion=setup_org["archivo_org"],
            numero_gde="B",
        )
