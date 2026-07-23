"""Tests del endpoint mobile de territoriales de comedores."""

import io

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from comedores.models import Comedor, ImagenComedor
from core.models import Provincia
from relevamientos.models import Relevamiento
from users.models import TerritorialComedorProvincia


def _png_upload(name="foto.png"):
    buffer = io.BytesIO()
    Image.new("RGB", (2, 2), color="red").save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


def _make_territorial(username, provincias):
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="testpass123",
    )
    user.profile.es_territorial_comedor = True
    user.profile.save(update_fields=["es_territorial_comedor"])
    for provincia in provincias:
        TerritorialComedorProvincia.objects.create(
            profile=user.profile, provincia=provincia
        )
    return user


def _auth_client(user):
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


@pytest.mark.django_db
def test_territorial_comedores_scoped_by_provincia():
    prov_a = Provincia.objects.create(nombre="Prov A")
    prov_b = Provincia.objects.create(nombre="Prov B")
    comedor_a = Comedor.objects.create(nombre="Comedor A", provincia=prov_a)
    Comedor.objects.create(nombre="Comedor B", provincia=prov_b)

    user = _make_territorial("terr_scope", [prov_a])
    client = _auth_client(user)

    response = client.get("/api/territorial/comedores/")

    assert response.status_code == 200
    ids = [row["id"] for row in response.data["results"]]
    assert ids == [comedor_a.id]
    assert [prov["nombre"] for prov in response.data["provincias"]] == ["Prov A"]


@pytest.mark.django_db
def test_territorial_comedores_includes_relevamiento_summary():
    prov = Provincia.objects.create(nombre="Prov Rel")
    comedor = Comedor.objects.create(nombre="Comedor Rel", provincia=prov)
    Relevamiento.objects.create(comedor=comedor, estado="Visita pendiente")

    user = _make_territorial("terr_rel", [prov])
    client = _auth_client(user)

    response = client.get("/api/territorial/comedores/")

    assert response.status_code == 200
    row = next(r for r in response.data["results"] if r["id"] == comedor.id)
    assert row["relevamientos"]["total"] == 1
    assert row["relevamientos"]["ultimo"]["estado"] == "Visita pendiente"


@pytest.mark.django_db
def test_territorial_comedores_items_lista_todos_los_relevamientos():
    from django.utils import timezone

    prov = Provincia.objects.create(nombre="Prov Items")
    comedor = Comedor.objects.create(nombre="Comedor Items", provincia=prov)
    # Finalizado con fecha reciente + pendiente sin fecha (el caso del bug).
    finalizado = Relevamiento.objects.create(
        comedor=comedor, estado="Finalizado", fecha_visita=timezone.now()
    )
    pendiente = Relevamiento.objects.create(
        comedor=comedor, estado="Visita pendiente"
    )

    user = _make_territorial("terr_items", [prov])
    client = _auth_client(user)

    response = client.get("/api/territorial/comedores/")

    assert response.status_code == 200
    row = next(r for r in response.data["results"] if r["id"] == comedor.id)
    relevamientos = row["relevamientos"]
    assert relevamientos["total"] == 2
    ids = {item["id"] for item in relevamientos["items"]}
    assert ids == {finalizado.id, pendiente.id}
    # El pendiente debe estar presente aunque `ultimo` sea el finalizado.
    estados = {item["id"]: item["estado"] for item in relevamientos["items"]}
    assert estados[pendiente.id] == "Visita pendiente"
    assert estados[finalizado.id] == "Finalizado"


@pytest.mark.django_db
def test_territorial_comedores_expone_seguimientos_items():
    from relevamientos.models import PrimerSeguimiento

    prov = Provincia.objects.create(nombre="Prov Seg")
    comedor = Comedor.objects.create(nombre="Comedor Seg", provincia=prov)
    rel = Relevamiento.objects.create(comedor=comedor, estado="Visita pendiente")
    seg = PrimerSeguimiento.objects.create(id_relevamiento=rel, estado="Asignado")

    user = _make_territorial("terr_seg", [prov])
    client = _auth_client(user)

    response = client.get("/api/territorial/comedores/")

    assert response.status_code == 200
    row = next(r for r in response.data["results"] if r["id"] == comedor.id)
    segs = row["seguimientos"]
    assert segs["total"] == 1
    item = segs["items"][0]
    assert item["id"] == seg.id
    assert item["estado"] == "Asignado"
    assert item["id_relevamiento"] == rel.id


@pytest.mark.django_db
def test_territorial_detail_scoped_by_provincia():
    prov_a = Provincia.objects.create(nombre="Prov Det A")
    prov_b = Provincia.objects.create(nombre="Prov Det B")
    comedor_a = Comedor.objects.create(nombre="Comedor Det A", provincia=prov_a)
    comedor_b = Comedor.objects.create(nombre="Comedor Det B", provincia=prov_b)

    user = _make_territorial("terr_det", [prov_a])
    client = _auth_client(user)

    ok = client.get(f"/api/territorial/comedores/{comedor_a.id}/")
    assert ok.status_code == 200
    assert ok.data["id"] == comedor_a.id

    fuera = client.get(f"/api/territorial/comedores/{comedor_b.id}/")
    assert fuera.status_code == 404


@pytest.mark.django_db
def test_territorial_detail_includes_relevamiento_actual_mobile():
    prov = Provincia.objects.create(nombre="Prov Precarga")
    comedor = Comedor.objects.create(nombre="Comedor Precarga", provincia=prov)
    relevamiento = Relevamiento.objects.create(
        comedor=comedor, estado="Visita pendiente"
    )

    user = _make_territorial("terr_precarga", [prov])
    client = _auth_client(user)

    response = client.get(f"/api/territorial/comedores/{comedor.id}/")

    assert response.status_code == 200
    actual = response.data["relevamiento_actual_mobile"]
    assert actual is not None
    assert actual["id"] == relevamiento.id
    assert "sections" in actual
    # Las secciones basadas en el modelo traen la clave del campo (snake_case) y el
    # valor crudo, para que la PWA prellene el formulario 1:1. La sección
    # "Información" es un resumen legible (display) y no lleva `campo`.
    model_section_items = [
        it
        for sec in actual["sections"]
        if sec["titulo"] != "Información"
        for it in sec["items"]
    ]
    assert model_section_items, "se esperaban items en las secciones del modelo"
    for it in model_section_items:
        assert "campo" in it and "valor" in it
        assert "pregunta" in it and "respuesta" in it


@pytest.mark.django_db
def test_territorial_uploads_image_to_scoped_comedor():
    prov = Provincia.objects.create(nombre="Prov Img")
    comedor = Comedor.objects.create(nombre="Comedor Img", provincia=prov)

    user = _make_territorial("terr_img", [prov])
    client = _auth_client(user)

    response = client.post(
        f"/api/territorial/comedores/{comedor.id}/imagenes/",
        {"imagen": _png_upload()},
        format="multipart",
    )

    assert response.status_code == 201
    assert len(response.data["imagenes"]) == 1
    assert response.data["imagenes"][0]["url"]
    assert ImagenComedor.objects.filter(comedor=comedor, origen="mobile").count() == 1


@pytest.mark.django_db
def test_territorial_image_dedup_by_client_uuid():
    prov = Provincia.objects.create(nombre="Prov Dedup")
    comedor = Comedor.objects.create(nombre="Comedor Dedup", provincia=prov)

    user = _make_territorial("terr_dedup", [prov])
    client = _auth_client(user)
    url = f"/api/territorial/comedores/{comedor.id}/imagenes/"

    first = client.post(
        url,
        {"imagen": _png_upload("a.png"), "client_uuid": "foto-1"},
        format="multipart",
    )
    assert first.status_code == 201

    # Reintento offline con el mismo client_uuid: no debe duplicar.
    retry = client.post(
        url,
        {"imagen": _png_upload("a.png"), "client_uuid": "foto-1"},
        format="multipart",
    )
    assert retry.status_code == 200

    assert ImagenComedor.objects.filter(comedor=comedor).count() == 1


@pytest.mark.django_db
def test_territorial_uploads_firma_returns_url():
    prov = Provincia.objects.create(nombre="Prov Firma")
    comedor = Comedor.objects.create(nombre="Comedor Firma", provincia=prov)

    user = _make_territorial("terr_firma", [prov])
    client = _auth_client(user)

    response = client.post(
        f"/api/territorial/comedores/{comedor.id}/firma/",
        {"firma": _png_upload("firma.png")},
        format="multipart",
    )

    assert response.status_code == 201
    assert response.data["url"].startswith("http")
    # La firma NO se registra como foto del comedor.
    assert ImagenComedor.objects.filter(comedor=comedor).count() == 0


@pytest.mark.django_db
def test_territorial_upload_image_scoped_to_relevamiento():
    prov = Provincia.objects.create(nombre="Prov ImgRel")
    comedor = Comedor.objects.create(nombre="Comedor ImgRel", provincia=prov)
    rel = Relevamiento.objects.create(comedor=comedor, estado="Visita pendiente")

    user = _make_territorial("terr_imgrel", [prov])
    client = _auth_client(user)

    resp = client.post(
        f"/api/territorial/comedores/{comedor.id}/imagenes/",
        {"imagen": _png_upload(), "sisoc_id": rel.id},
        format="multipart",
    )

    assert resp.status_code == 201
    assert resp.data["imagenes"][0]["relevamiento"] == rel.id
    assert (
        ImagenComedor.objects.filter(comedor=comedor, relevamiento=rel).count() == 1
    )


@pytest.mark.django_db
def test_territorial_upload_image_rejects_relevamiento_de_otro_comedor():
    prov_a = Provincia.objects.create(nombre="Prov ImgA")
    prov_b = Provincia.objects.create(nombre="Prov ImgB")
    comedor_a = Comedor.objects.create(nombre="Comedor ImgA", provincia=prov_a)
    comedor_b = Comedor.objects.create(nombre="Comedor ImgB", provincia=prov_b)
    rel_b = Relevamiento.objects.create(comedor=comedor_b, estado="Visita pendiente")

    user = _make_territorial("terr_imginv", [prov_a])
    client = _auth_client(user)

    resp = client.post(
        f"/api/territorial/comedores/{comedor_a.id}/imagenes/",
        {"imagen": _png_upload(), "sisoc_id": rel_b.id},
        format="multipart",
    )

    assert resp.status_code == 400
    assert ImagenComedor.objects.filter(comedor=comedor_a).count() == 0


@pytest.mark.django_db
def test_territorial_cannot_upload_image_outside_scope():
    prov_a = Provincia.objects.create(nombre="Prov Img A")
    prov_b = Provincia.objects.create(nombre="Prov Img B")
    comedor_b = Comedor.objects.create(nombre="Comedor Img B", provincia=prov_b)

    user = _make_territorial("terr_img_scope", [prov_a])
    client = _auth_client(user)

    response = client.post(
        f"/api/territorial/comedores/{comedor_b.id}/imagenes/",
        {"imagen": _png_upload()},
        format="multipart",
    )

    assert response.status_code == 404
    assert ImagenComedor.objects.filter(comedor=comedor_b).count() == 0


@pytest.mark.django_db
def test_territorial_endpoint_rejects_non_territorial():
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="no_terr",
        email="no_terr@example.com",
        password="testpass123",
    )
    client = _auth_client(user)

    response = client.get("/api/territorial/comedores/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_territorial_endpoint_requires_authentication():
    client = APIClient()

    response = client.get("/api/territorial/comedores/")

    assert response.status_code == 401
