"""Tests del endpoint mobile de territoriales de comedores."""

import io
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import close_old_connections, connection
from PIL import Image
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from comedores.models import Comedor, ImagenComedor, Programas, TipoDeComedor
from core.models import Localidad, Municipio, Provincia
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


def _create_comedor_payload(provincia, **overrides):
    payload = {
        "client_uuid": "loc_comedor_creacion_1",
        "nombre": "Comedor creado desde Gestionar",
        "tipo": "Comedor",
        "programa": "Alimentar comunidad",
        "provincia": provincia.nombre,
        "municipio": "Municipio de prueba",
        "localidad": "Localidad de prueba",
        "calle": "Calle 123",
        "numero": 45,
        "codigo_postal": 1000,
        "latitud": -34.6,
        "longitud": -58.4,
    }
    payload.update(overrides)
    return payload


def _create_comedor_catalogos(provincia):
    municipio = Municipio.objects.create(
        nombre="Municipio de prueba", provincia=provincia
    )
    Localidad.objects.create(nombre="Localidad de prueba", municipio=municipio)
    TipoDeComedor.objects.create(nombre="Comedor")
    Programas.objects.create(nombre="Alimentar comunidad")


@pytest.mark.django_db
def test_territorial_crea_comedor_y_devuelve_contrato_territorial():
    provincia = Provincia.objects.create(nombre="Provincia alta")
    _create_comedor_catalogos(provincia)
    user = _make_territorial("terr_create", [provincia])

    response = _auth_client(user).post(
        "/api/territorial/comedores/",
        _create_comedor_payload(provincia),
        format="json",
    )

    assert response.status_code == 201
    assert response.data["id"]
    assert response.data["nombre"] == "Comedor creado desde Gestionar"
    assert response.data["provincia"] == provincia.nombre
    assert response.data["municipio"] == "Municipio de prueba"
    assert response.data["localidad"] == "Localidad de prueba"
    assert response.data["tipo"] == "Comedor"
    assert response.data["programa"] == "Alimentar comunidad"
    assert Comedor.objects.filter(nombre="Comedor creado desde Gestionar").count() == 1


@pytest.mark.django_db
def test_territorial_alta_requiere_token_rol_y_payload_relacionado_valido():
    provincia = Provincia.objects.create(nombre="Provincia validacion")
    _create_comedor_catalogos(provincia)
    payload = _create_comedor_payload(provincia)
    anonimo = APIClient()
    usuario_comun = get_user_model().objects.create_user(
        username="sin_rol_territorial",
        password="testpass123",
    )
    territorial = _auth_client(_make_territorial("terr_invalid", [provincia]))

    missing_token = anonimo.post("/api/territorial/comedores/", payload, format="json")
    missing_role = _auth_client(usuario_comun).post(
        "/api/territorial/comedores/", payload, format="json"
    )
    invalid_relation = territorial.post(
        "/api/territorial/comedores/",
        {**payload, "municipio": "Municipio inexistente"},
        format="json",
    )

    assert missing_token.status_code == 401
    assert missing_role.status_code == 403
    assert invalid_relation.status_code == 400
    assert Comedor.objects.filter(provincia=provincia).count() == 0


@pytest.mark.django_db
def test_territorial_reintento_de_alta_es_idempotente_y_rechaza_otro_payload():
    provincia = Provincia.objects.create(nombre="Provincia idem")
    _create_comedor_catalogos(provincia)
    client = _auth_client(_make_territorial("terr_idem", [provincia]))
    payload = _create_comedor_payload(provincia)

    first = client.post("/api/territorial/comedores/", payload, format="json")
    retry = client.post("/api/territorial/comedores/", payload, format="json")
    conflict = client.post(
        "/api/territorial/comedores/",
        {**payload, "nombre": "Payload distinto"},
        format="json",
    )

    assert first.status_code == 201
    assert retry.status_code == 200
    assert retry.data["id"] == first.data["id"]
    assert conflict.status_code == 409
    assert Comedor.objects.filter(provincia=provincia).count() == 1


@pytest.mark.django_db
def test_territorial_reintento_no_depende_de_catalogos_renombrados():
    provincia = Provincia.objects.create(nombre="Provincia catálogo mutable")
    _create_comedor_catalogos(provincia)
    client = _auth_client(_make_territorial("terr_catalogo_replay", [provincia]))
    payload = _create_comedor_payload(provincia)

    first = client.post("/api/territorial/comedores/", payload, format="json")
    TipoDeComedor.objects.filter(nombre="Comedor").update(nombre="Comedor renombrado")
    replay = client.post("/api/territorial/comedores/", payload, format="json")

    assert first.status_code == 201
    assert replay.status_code == 200
    assert replay.data["id"] == first.data["id"]


@pytest.mark.django_db
def test_territorial_revalida_alcance_en_reintento_y_aisla_claves_por_usuario():
    provincia = Provincia.objects.create(nombre="Provincia aislamiento")
    _create_comedor_catalogos(provincia)
    user_a = _make_territorial("terr_idem_a", [provincia])
    user_b = _make_territorial("terr_idem_b", [provincia])
    payload = _create_comedor_payload(provincia)

    first = _auth_client(user_a).post(
        "/api/territorial/comedores/", payload, format="json"
    )
    same_key_other_user = _auth_client(user_b).post(
        "/api/territorial/comedores/",
        {**payload, "nombre": "Comedor de otro usuario"},
        format="json",
    )
    user_a.profile.territorial_comedor_provincias.all().delete()
    replay_without_scope = _auth_client(user_a).post(
        "/api/territorial/comedores/", payload, format="json"
    )

    assert first.status_code == 201
    assert same_key_other_user.status_code == 201
    assert same_key_other_user.data["id"] != first.data["id"]
    assert replay_without_scope.status_code == 403


@pytest.mark.django_db
def test_territorial_rechaza_alta_fuera_del_alcance_y_edita_solo_su_provincia():
    provincia_permitida = Provincia.objects.create(nombre="Provincia permitida")
    provincia_ajena = Provincia.objects.create(nombre="Provincia ajena")
    _create_comedor_catalogos(provincia_permitida)
    _create_comedor_catalogos(provincia_ajena)
    user = _make_territorial("terr_write_scope", [provincia_permitida])
    client = _auth_client(user)
    propio = Comedor.objects.create(nombre="Propio", provincia=provincia_permitida)
    ajeno = Comedor.objects.create(nombre="Ajeno", provincia=provincia_ajena)

    outside = client.post(
        "/api/territorial/comedores/",
        _create_comedor_payload(provincia_ajena),
        format="json",
    )
    updated = client.patch(
        f"/api/territorial/comedores/{propio.id}/",
        {"nombre": "Propio editado"},
        format="json",
    )
    forbidden_update = client.patch(
        f"/api/territorial/comedores/{ajeno.id}/",
        {"nombre": "No debe editarse"},
        format="json",
    )

    assert outside.status_code == 403
    assert updated.status_code == 200
    assert updated.data["nombre"] == "Propio editado"
    assert forbidden_update.status_code == 404
    ajeno.refresh_from_db()
    assert ajeno.nombre == "Ajeno"


@pytest.mark.django_db
def test_territorial_patch_conserva_jerarquia_geografica():
    provincia_a = Provincia.objects.create(nombre="Provincia jerarquía A")
    provincia_b = Provincia.objects.create(nombre="Provincia jerarquía B")
    _create_comedor_catalogos(provincia_a)
    _create_comedor_catalogos(provincia_b)
    municipio_a = Municipio.objects.get(
        provincia=provincia_a, nombre="Municipio de prueba"
    )
    localidad_a = Localidad.objects.get(
        municipio=municipio_a, nombre="Localidad de prueba"
    )
    municipio_alterno = Municipio.objects.create(
        nombre="Municipio alterno", provincia=provincia_a
    )
    localidad_alterna = Localidad.objects.create(
        nombre="Localidad alterna", municipio=municipio_alterno
    )
    comedor = Comedor.objects.create(
        nombre="Comedor geográfico",
        provincia=provincia_a,
        municipio=municipio_a,
        localidad=localidad_a,
    )
    client = _auth_client(
        _make_territorial("terr_geografia", [provincia_a, provincia_b])
    )

    incomplete_province = client.patch(
        f"/api/territorial/comedores/{comedor.id}/",
        {"provincia": provincia_b.nombre},
        format="json",
    )
    incomplete_municipio = client.patch(
        f"/api/territorial/comedores/{comedor.id}/",
        {"municipio": municipio_alterno.nombre},
        format="json",
    )
    completed_municipio = client.patch(
        f"/api/territorial/comedores/{comedor.id}/",
        {
            "municipio": municipio_alterno.nombre,
            "localidad": localidad_alterna.nombre,
        },
        format="json",
    )

    comedor.refresh_from_db()
    assert incomplete_province.status_code == 400
    assert incomplete_municipio.status_code == 400
    assert completed_municipio.status_code == 200
    assert comedor.provincia_id == provincia_a.id
    assert comedor.municipio_id == municipio_alterno.id
    assert comedor.localidad_id == localidad_alterna.id


@pytest.mark.django_db
def test_territorial_rechaza_fecha_iso_invalida():
    provincia = Provincia.objects.create(nombre="Provincia fecha")
    _create_comedor_catalogos(provincia)
    client = _auth_client(_make_territorial("terr_fecha", [provincia]))

    response = client.post(
        "/api/territorial/comedores/",
        _create_comedor_payload(provincia, comienzo="2020-99-99"),
        format="json",
    )

    assert response.status_code == 400
    assert "comienzo" in response.data


@pytest.mark.mysql_compat
@pytest.mark.django_db(transaction=True)
def test_territorial_alta_concurrente_con_misma_clave_crea_un_solo_comedor():
    if connection.vendor != "mysql":
        pytest.skip(
            "La garantía de concurrencia se valida contra MySQL, como producción."
        )

    provincia = Provincia.objects.create(nombre="Provincia concurrente")
    _create_comedor_catalogos(provincia)
    user = _make_territorial("terr_concurrent", [provincia])
    token, _ = Token.objects.get_or_create(user=user)
    payload = _create_comedor_payload(provincia)

    def post_same_operation():
        close_old_connections()
        try:
            client = APIClient()
            client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
            response = client.post(
                "/api/territorial/comedores/", payload, format="json"
            )
            return response.status_code, response.data["id"]
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: post_same_operation(), range(2)))

    assert sorted(status for status, _ in results) == [200, 201]
    assert len({remote_id for _, remote_id in results}) == 1
    assert Comedor.objects.filter(provincia=provincia).count() == 1


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
