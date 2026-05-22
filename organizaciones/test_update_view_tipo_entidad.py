"""Tests para la Seccion 2 del issue #1605: al cambiar el ``tipo_entidad`` de
una ``Organizacion`` desde el legajo, el listado de documentos
(``ArchivoOrganizacion``) debe reiniciarse."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client
from django.urls import reverse

from core.models import Provincia
from organizaciones.models import (
    ArchivoOrganizacion,
    DocumentacionOrganizacion,
    Organizacion,
    TipoEntidad,
)


pytestmark = pytest.mark.django_db
User = get_user_model()


@pytest.fixture
def usuario():
    user = User.objects.create_user(username="org_editor", password="pwd")
    permiso = Permission.objects.get(
        content_type__app_label="organizaciones", codename="view_organizacion"
    )
    user.user_permissions.add(permiso)
    return user


@pytest.fixture
def tipos():
    juridica = TipoEntidad.objects.create(nombre="Personería Jurídica")
    eclesiastica = TipoEntidad.objects.create(
        nombre="Personería Jurídica Eclesiástica"
    )
    return {"juridica": juridica, "eclesiastica": eclesiastica}


@pytest.fixture
def provincia():
    return Provincia.objects.create(nombre="Buenos Aires")


@pytest.fixture
def organizacion_con_documentos(tipos, provincia):
    organizacion = Organizacion.objects.create(
        nombre="Org con docs", tipo_entidad=tipos["juridica"], provincia=provincia
    )
    doc_a = DocumentacionOrganizacion.objects.create(
        nombre="Acta Constitutiva",
        categoria=DocumentacionOrganizacion.CATEGORIA_PERSONERIA,
        obligatorio=True,
    )
    doc_b = DocumentacionOrganizacion.objects.create(
        nombre="Estatuto",
        categoria=DocumentacionOrganizacion.CATEGORIA_PERSONERIA,
        obligatorio=True,
    )
    ArchivoOrganizacion.objects.create(
        organizacion=organizacion,
        documentacion=doc_a,
        archivo="organizaciones/test-a.pdf",
        estado=ArchivoOrganizacion.ESTADO_ACEPTADO,
    )
    ArchivoOrganizacion.objects.create(
        organizacion=organizacion,
        documentacion=doc_b,
        archivo="organizaciones/test-b.pdf",
        estado=ArchivoOrganizacion.ESTADO_A_VALIDAR,
    )
    return organizacion


def _post_payload(organizacion, tipo_entidad):
    return {
        "nombre": organizacion.nombre,
        "cuit": "",
        "telefono": "",
        "email": "",
        "domicilio": "",
        "localidad": "",
        "partido": "",
        "provincia": str(organizacion.provincia_id),
        "municipio": "",
        "tipo_entidad": str(tipo_entidad.pk),
        "subtipo_entidad": "",
        "fecha_vencimiento": "2030-01-01",
        "sigla": "",
        "cuil_duplicado_confirmado": "",
        "cuil_duplicado_confirmado_valor": "",
    }


def test_cambio_tipo_entidad_borra_todos_los_archivos(
    organizacion_con_documentos, tipos, usuario
):
    client = Client()
    client.force_login(usuario)
    url = reverse("organizacion_editar", kwargs={"pk": organizacion_con_documentos.pk})

    response = client.post(
        url, _post_payload(organizacion_con_documentos, tipos["eclesiastica"])
    )

    assert response.status_code in (302, 303), response.content[:300]
    organizacion_con_documentos.refresh_from_db()
    assert organizacion_con_documentos.tipo_entidad_id == tipos["eclesiastica"].pk
    assert (
        ArchivoOrganizacion.objects.filter(
            organizacion=organizacion_con_documentos
        ).count()
        == 0
    ), "Al cambiar tipo_entidad todos los ArchivoOrganizacion deben borrarse"


def test_sin_cambio_de_tipo_entidad_no_borra_archivos(
    organizacion_con_documentos, tipos, usuario
):
    client = Client()
    client.force_login(usuario)
    url = reverse("organizacion_editar", kwargs={"pk": organizacion_con_documentos.pk})

    response = client.post(
        url, _post_payload(organizacion_con_documentos, tipos["juridica"])
    )

    assert response.status_code in (302, 303)
    assert (
        ArchivoOrganizacion.objects.filter(
            organizacion=organizacion_con_documentos
        ).count()
        == 2
    ), "Si tipo_entidad no cambia, los archivos deben preservarse"


def test_volver_al_tipo_anterior_no_recupera_archivos_borrados(
    organizacion_con_documentos, tipos, usuario
):
    """2.2 — Si despues de cambiar se vuelve al tipo anterior, los archivos
    eliminados NO se recuperan: el listado debe seguir vacio."""

    client = Client()
    client.force_login(usuario)
    url = reverse("organizacion_editar", kwargs={"pk": organizacion_con_documentos.pk})

    # Primer cambio: eclesiastica → borra todo
    client.post(
        url, _post_payload(organizacion_con_documentos, tipos["eclesiastica"])
    )
    # Volver al tipo anterior
    client.post(
        url, _post_payload(organizacion_con_documentos, tipos["juridica"])
    )

    organizacion_con_documentos.refresh_from_db()
    assert organizacion_con_documentos.tipo_entidad_id == tipos["juridica"].pk
    assert (
        ArchivoOrganizacion.objects.filter(
            organizacion=organizacion_con_documentos
        ).count()
        == 0
    )
