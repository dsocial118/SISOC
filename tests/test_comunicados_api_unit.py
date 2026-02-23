"""Tests de la API REST para el módulo de comunicados (PWA)."""

from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from comedores.models import Comedor
from comunicados.models import (
    Comunicado,
    ComunicadoAdjunto,
    EstadoComunicado,
    SubtipoComunicado,
    TipoComunicado,
)

pytestmark = pytest.mark.django_db


# =============================================================================
# Helpers
# =============================================================================

def _create_admin(username: str = "admin_api") -> User:
    return User.objects.create_superuser(username, f"{username}@test.com", "test")


def _comunicado_base(usuario_creador: User, subtipo: str, titulo: str | None = None, estado: str = EstadoComunicado.PUBLICADO, fecha_vencimiento=None) -> Comunicado:
    return Comunicado.objects.create(
        titulo=titulo or f"API {subtipo} {estado}",
        cuerpo="Contenido API",
        estado=estado,
        tipo=TipoComunicado.EXTERNO,
        subtipo=subtipo,
        fecha_publicacion=timezone.now() if estado == EstadoComunicado.PUBLICADO else None,
        fecha_vencimiento=fecha_vencimiento,
        usuario_creador=usuario_creador,
    )


def _create_comunicado(*, usuario_creador: User, subtipo: str, titulo: str | None = None, estado: str = EstadoComunicado.PUBLICADO, fecha_vencimiento=None, comedores=None) -> Comunicado:
    c = _comunicado_base(usuario_creador, subtipo, titulo, estado, fecha_vencimiento)
    if comedores:
        c.comedores.set(comedores)
    return c


# =============================================================================
# API Institucional - GET /api/comunicados/institucional/
# =============================================================================

def test_api_institucional_devuelve_lista_con_api_key(api_client):
    admin = _create_admin("admin_inst_list")
    _create_comunicado(usuario_creador=admin, subtipo=SubtipoComunicado.INSTITUCIONAL)

    response = api_client.get("/api/comunicados/institucional/")

    assert response.status_code == 200
    assert len(response.data["results"]) == 1


def test_api_institucional_sin_autenticacion_devuelve_401(client):
    response = client.get("/api/comunicados/institucional/")

    assert response.status_code == 401


def test_api_institucional_solo_devuelve_publicados(api_client):
    admin = _create_admin("admin_inst_pub")
    _create_comunicado(
        usuario_creador=admin,
        subtipo=SubtipoComunicado.INSTITUCIONAL,
        estado=EstadoComunicado.PUBLICADO,
        titulo="Publicado inst",
    )
    _create_comunicado(
        usuario_creador=admin,
        subtipo=SubtipoComunicado.INSTITUCIONAL,
        estado=EstadoComunicado.BORRADOR,
        titulo="Borrador inst",
    )
    _create_comunicado(
        usuario_creador=admin,
        subtipo=SubtipoComunicado.INSTITUCIONAL,
        estado=EstadoComunicado.ARCHIVADO,
        titulo="Archivado inst",
    )

    response = api_client.get("/api/comunicados/institucional/")

    assert response.status_code == 200
    titulos = [item["titulo"] for item in response.data["results"]]
    assert "Publicado inst" in titulos
    assert "Borrador inst" not in titulos
    assert "Archivado inst" not in titulos


def test_api_institucional_no_devuelve_vencidos(api_client):
    admin = _create_admin("admin_inst_venc")
    _create_comunicado(
        usuario_creador=admin,
        subtipo=SubtipoComunicado.INSTITUCIONAL,
        titulo="Vencido inst",
        fecha_vencimiento=timezone.now() - timedelta(days=1),
    )
    _create_comunicado(
        usuario_creador=admin,
        subtipo=SubtipoComunicado.INSTITUCIONAL,
        titulo="Vigente inst",
        fecha_vencimiento=timezone.now() + timedelta(days=1),
    )

    response = api_client.get("/api/comunicados/institucional/")

    titulos = [item["titulo"] for item in response.data["results"]]
    assert "Vencido inst" not in titulos
    assert "Vigente inst" in titulos


def test_api_institucional_sin_fecha_vencimiento_aparece(api_client):
    admin = _create_admin("admin_inst_sin_venc")
    _create_comunicado(
        usuario_creador=admin,
        subtipo=SubtipoComunicado.INSTITUCIONAL,
        titulo="Sin vencimiento inst",
        fecha_vencimiento=None,
    )

    response = api_client.get("/api/comunicados/institucional/")

    titulos = [item["titulo"] for item in response.data["results"]]
    assert "Sin vencimiento inst" in titulos


def test_api_institucional_no_devuelve_tipo_comedores(api_client):
    admin = _create_admin("admin_inst_no_com")
    comedor = Comedor.objects.create(nombre="Comedor API test")
    _create_comunicado(
        usuario_creador=admin,
        subtipo=SubtipoComunicado.INSTITUCIONAL,
        titulo="Institucional",
    )
    _create_comunicado(
        usuario_creador=admin,
        subtipo=SubtipoComunicado.COMEDORES,
        titulo="A comedores",
        comedores=[comedor],
    )

    response = api_client.get("/api/comunicados/institucional/")

    titulos = [item["titulo"] for item in response.data["results"]]
    assert "Institucional" in titulos
    assert "A comedores" not in titulos


def test_api_institucional_no_devuelve_comunicados_internos(api_client):
    admin = _create_admin("admin_inst_no_int")
    Comunicado.objects.create(
        titulo="Interno que no debe aparecer",
        cuerpo="Contenido",
        estado=EstadoComunicado.PUBLICADO,
        tipo=TipoComunicado.INTERNO,
        fecha_publicacion=timezone.now(),
        usuario_creador=admin,
    )
    _create_comunicado(
        usuario_creador=admin,
        subtipo=SubtipoComunicado.INSTITUCIONAL,
        titulo="Institucional que sí aparece",
    )

    response = api_client.get("/api/comunicados/institucional/")

    titulos = [item["titulo"] for item in response.data["results"]]
    assert "Interno que no debe aparecer" not in titulos
    assert "Institucional que sí aparece" in titulos


def test_api_institucional_incluye_adjuntos_en_respuesta(api_client):
    admin = _create_admin("admin_inst_adj")
    from django.core.files.uploadedfile import SimpleUploadedFile

    comunicado = _create_comunicado(
        usuario_creador=admin,
        subtipo=SubtipoComunicado.INSTITUCIONAL,
        titulo="Inst con adjunto",
    )
    ComunicadoAdjunto.objects.create(
        comunicado=comunicado,
        archivo=SimpleUploadedFile("doc.pdf", b"%PDF-1.4", content_type="application/pdf"),
        nombre_original="doc.pdf",
    )

    response = api_client.get("/api/comunicados/institucional/")

    resultado = next(
        item for item in response.data["results"] if item["titulo"] == "Inst con adjunto"
    )
    assert len(resultado["adjuntos"]) == 1
    assert resultado["adjuntos"][0]["nombre_original"] == "doc.pdf"


def test_api_institucional_campos_esperados_en_respuesta(api_client):
    admin = _create_admin("admin_inst_campos")
    _create_comunicado(
        usuario_creador=admin,
        subtipo=SubtipoComunicado.INSTITUCIONAL,
        titulo="Campos inst",
    )

    response = api_client.get("/api/comunicados/institucional/")

    resultado = response.data["results"][0]
    for campo in ["id", "titulo", "cuerpo", "estado", "subtipo", "fecha_publicacion", "adjuntos"]:
        assert campo in resultado


# =============================================================================
# API Comedor - GET /api/comunicados/comedor/{comedor_id}/
# =============================================================================

def test_api_comedor_devuelve_comunicados_del_comedor(api_client):
    admin = _create_admin("admin_com_list")
    comedor = Comedor.objects.create(nombre="Comedor API")
    _create_comunicado(
        usuario_creador=admin,
        subtipo=SubtipoComunicado.COMEDORES,
        titulo="Para este comedor",
        comedores=[comedor],
    )

    response = api_client.get(f"/api/comunicados/comedor/{comedor.pk}/")

    assert response.status_code == 200
    titulos = [item["titulo"] for item in response.data["results"]]
    assert "Para este comedor" in titulos


def test_api_comedor_sin_autenticacion_devuelve_401(client):
    comedor = Comedor.objects.create(nombre="Comedor sin auth")

    response = client.get(f"/api/comunicados/comedor/{comedor.pk}/")

    assert response.status_code == 401


def test_api_comedor_no_devuelve_comunicados_de_otro_comedor(api_client):
    admin = _create_admin("admin_com_otro")
    comedor_a = Comedor.objects.create(nombre="Comedor A")
    comedor_b = Comedor.objects.create(nombre="Comedor B")
    _create_comunicado(
        usuario_creador=admin,
        subtipo=SubtipoComunicado.COMEDORES,
        titulo="Solo para A",
        comedores=[comedor_a],
    )
    _create_comunicado(
        usuario_creador=admin,
        subtipo=SubtipoComunicado.COMEDORES,
        titulo="Solo para B",
        comedores=[comedor_b],
    )

    response = api_client.get(f"/api/comunicados/comedor/{comedor_a.pk}/")

    titulos = [item["titulo"] for item in response.data["results"]]
    assert "Solo para A" in titulos
    assert "Solo para B" not in titulos


def test_api_comedor_solo_devuelve_publicados(api_client):
    admin = _create_admin("admin_com_pub")
    comedor = Comedor.objects.create(nombre="Comedor pub")
    _create_comunicado(
        usuario_creador=admin,
        subtipo=SubtipoComunicado.COMEDORES,
        estado=EstadoComunicado.PUBLICADO,
        titulo="Publicado com",
        comedores=[comedor],
    )
    _create_comunicado(
        usuario_creador=admin,
        subtipo=SubtipoComunicado.COMEDORES,
        estado=EstadoComunicado.BORRADOR,
        titulo="Borrador com",
        comedores=[comedor],
    )

    response = api_client.get(f"/api/comunicados/comedor/{comedor.pk}/")

    titulos = [item["titulo"] for item in response.data["results"]]
    assert "Publicado com" in titulos
    assert "Borrador com" not in titulos


def test_api_comedor_no_devuelve_vencidos(api_client):
    admin = _create_admin("admin_com_venc")
    comedor = Comedor.objects.create(nombre="Comedor venc")
    _create_comunicado(
        usuario_creador=admin,
        subtipo=SubtipoComunicado.COMEDORES,
        titulo="Vencido com",
        fecha_vencimiento=timezone.now() - timedelta(days=1),
        comedores=[comedor],
    )
    _create_comunicado(
        usuario_creador=admin,
        subtipo=SubtipoComunicado.COMEDORES,
        titulo="Vigente com",
        fecha_vencimiento=timezone.now() + timedelta(days=1),
        comedores=[comedor],
    )

    response = api_client.get(f"/api/comunicados/comedor/{comedor.pk}/")

    titulos = [item["titulo"] for item in response.data["results"]]
    assert "Vencido com" not in titulos
    assert "Vigente com" in titulos


def test_api_comedor_no_devuelve_institucionales(api_client):
    admin = _create_admin("admin_com_no_inst")
    comedor = Comedor.objects.create(nombre="Comedor no inst")
    _create_comunicado(
        usuario_creador=admin,
        subtipo=SubtipoComunicado.COMEDORES,
        titulo="A comedores",
        comedores=[comedor],
    )
    _create_comunicado(
        usuario_creador=admin,
        subtipo=SubtipoComunicado.INSTITUCIONAL,
        titulo="Institucional no debe aparecer",
    )

    response = api_client.get(f"/api/comunicados/comedor/{comedor.pk}/")

    titulos = [item["titulo"] for item in response.data["results"]]
    assert "A comedores" in titulos
    assert "Institucional no debe aparecer" not in titulos


def test_api_comedor_sin_fecha_vencimiento_aparece(api_client):
    admin = _create_admin("admin_com_sin_venc")
    comedor = Comedor.objects.create(nombre="Comedor sin venc")
    _create_comunicado(
        usuario_creador=admin,
        subtipo=SubtipoComunicado.COMEDORES,
        titulo="Sin vencimiento com",
        fecha_vencimiento=None,
        comedores=[comedor],
    )

    response = api_client.get(f"/api/comunicados/comedor/{comedor.pk}/")

    titulos = [item["titulo"] for item in response.data["results"]]
    assert "Sin vencimiento com" in titulos


def test_api_comedor_inexistente_devuelve_lista_vacia(api_client):
    response = api_client.get("/api/comunicados/comedor/99999/")

    assert response.status_code == 200
    assert response.data["results"] == []
