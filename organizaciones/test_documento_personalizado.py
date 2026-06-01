"""Tests del Req 4 del issue #1799: Documentacion Adicional (personalizada) en
el legajo de la Organizacion."""

import json

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory

from comedores.models import Comedor
from duplas.models import Dupla
from organizaciones.models import ArchivoOrganizacion, Organizacion, TipoEntidad
from organizaciones.views import (
    _build_documentacion_organizacion_rows,
    agregar_documento_personalizado_organizacion,
)


pytestmark = pytest.mark.django_db
User = get_user_model()


@pytest.fixture
def superuser():
    return User.objects.create_superuser(username="su_org", password="pwd")


@pytest.fixture
def organizacion():
    tipo = TipoEntidad.objects.create(nombre="Personería Jurídica")
    return Organizacion.objects.create(nombre="Org Adicional", tipo_entidad=tipo)


def _post(user, organizacion_id, data, archivo=None):
    payload = dict(data)
    if archivo is not None:
        payload["archivo"] = archivo
    request = RequestFactory().post(
        f"/organizaciones/{organizacion_id}/documentacion/personalizada/agregar/",
        data=payload,
    )
    request.user = user
    return agregar_documento_personalizado_organizacion(request, organizacion_id)


def _archivo(nombre="adicional.pdf"):
    return SimpleUploadedFile(nombre, b"contenido", content_type="application/pdf")


def test_alta_personalizado_crea_archivo(superuser, organizacion):
    response = _post(
        superuser,
        organizacion.id,
        {"nombre": "Nota aclaratoria"},
        archivo=_archivo(),
    )
    assert response.status_code == 200
    data = json.loads(response.content)
    assert data["success"] is True

    archivo = ArchivoOrganizacion.objects.get(pk=data["archivo_id"])
    assert archivo.organizacion_id == organizacion.id
    assert archivo.documentacion_id is None
    assert archivo.es_personalizado is True
    assert archivo.nombre_personalizado == "Nota aclaratoria"
    assert archivo.estado == ArchivoOrganizacion.ESTADO_ADJUNTO


def test_alta_personalizado_requiere_nombre(superuser, organizacion):
    response = _post(superuser, organizacion.id, {"nombre": "   "}, archivo=_archivo())
    assert response.status_code == 400
    assert ArchivoOrganizacion.objects.count() == 0


def test_alta_personalizado_requiere_archivo(superuser, organizacion):
    response = _post(superuser, organizacion.id, {"nombre": "Sin archivo"})
    assert response.status_code == 400
    assert ArchivoOrganizacion.objects.count() == 0


def test_listado_incluye_personalizados(organizacion):
    ArchivoOrganizacion.objects.create(
        organizacion=organizacion,
        documentacion=None,
        nombre_personalizado="Extra 1",
        archivo="organizaciones/documentacion/extra-1.pdf",
        estado=ArchivoOrganizacion.ESTADO_ADJUNTO,
    )
    rows = _build_documentacion_organizacion_rows(organizacion)
    personalizados = [row for row in rows if row.get("es_personalizado")]
    assert len(personalizados) == 1
    assert personalizados[0]["archivo"].nombre_personalizado == "Extra 1"


def test_alta_personalizado_sin_permiso_de_envio(organizacion):
    """Un abogado de la dupla puede ver el legajo pero no cargar (eso es del
    tecnico), por lo que la vista responde 403."""
    abogado = User.objects.create_user(username="abogado_org", password="pwd")
    dupla = Dupla.objects.create(nombre="Dupla Org", estado="Activo", abogado=abogado)
    Comedor.objects.create(nombre="Comedor Org", organizacion=organizacion, dupla=dupla)

    response = _post(abogado, organizacion.id, {"nombre": "X"}, archivo=_archivo())
    assert response.status_code == 403
    assert ArchivoOrganizacion.objects.count() == 0
