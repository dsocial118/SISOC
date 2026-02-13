from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from admisiones.models.admisiones import Admision, InformeTecnico
from comedores.models import Comedor, ImagenComedor, Nomina
from core.models import Provincia
from rendicioncuentasmensual.models import DocumentacionAdjunta, RendicionCuentaMensual
from users.models import AccesoComedorPWA


@pytest.fixture
def comedores(db):
    provincia = Provincia.objects.create(nombre="Cordoba")
    comedor_1 = Comedor.objects.create(nombre="Comedor Uno", provincia=provincia)
    comedor_2 = Comedor.objects.create(nombre="Comedor Dos", provincia=provincia)
    return comedor_1, comedor_2


def _create_pwa_user(
    *,
    comedor,
    role,
    username,
    created_by=None,
    password="testpass123",
):
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password=password,
    )
    AccesoComedorPWA.objects.create(
        user=user,
        comedor=comedor,
        rol=role,
        creado_por=created_by,
        activo=True,
    )
    return user


def _token_client(user):
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


def _fake_value_for_field(field):
    if field.choices:
        return field.choices[0][0]
    if isinstance(field, models.EmailField):
        return "test@example.com"
    if isinstance(field, (models.CharField, models.TextField)):
        return "test"
    if isinstance(field, models.BooleanField):
        return False
    if isinstance(field, models.DecimalField):
        return 1
    if isinstance(field, models.FloatField):
        return 1.0
    if isinstance(field, models.DateTimeField):
        return date(2026, 1, 1)
    if isinstance(field, models.DateField):
        return date(2026, 1, 1)
    if isinstance(field, models.IntegerField):
        return 1
    return "test"


def _create_informe_tecnico(admision, **overrides):
    payload = {}
    for field in InformeTecnico._meta.fields:
        if field.primary_key or field.auto_created:
            continue
        if getattr(field, "auto_now", False) or getattr(field, "auto_now_add", False):
            continue
        if field.has_default():
            continue
        if isinstance(field, models.ForeignKey):
            continue
        if field.null:
            continue
        payload[field.name] = _fake_value_for_field(field)

    payload.update(
        {
            "admision": admision,
            "tipo": "base",
            "estado": "Iniciado",
            "estado_formulario": "finalizado",
        }
    )
    payload.update(overrides)
    return InformeTecnico.objects.create(**payload)


@pytest.mark.django_db
def test_comedor_api_requires_authentication(comedores):
    comedor_1, _ = comedores
    client = APIClient()
    response = client.get(f"/api/comedores/{comedor_1.id}/")
    assert response.status_code == 401


@pytest.mark.django_db
def test_comedor_api_accepts_non_pwa_token(comedores):
    comedor_1, _ = comedores
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="no_pwa",
        email="no_pwa@example.com",
        password="testpass123",
    )
    client = _token_client(user)
    response = client.get(f"/api/comedores/{comedor_1.id}/")
    assert response.status_code == 200
    assert response.data["id"] == comedor_1.id


@pytest.mark.django_db
def test_representante_scope_returns_404_for_unassigned_comedor(comedores):
    comedor_1, comedor_2 = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_scope",
    )
    client = _token_client(representante)

    ok_response = client.get(f"/api/comedores/{comedor_1.id}/")
    forbidden_scope_response = client.get(f"/api/comedores/{comedor_2.id}/")

    assert ok_response.status_code == 200
    assert forbidden_scope_response.status_code == 404


@pytest.mark.django_db
def test_representante_can_list_and_create_operadores(comedores):
    comedor_1, _ = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_users",
    )
    operador_existente = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_OPERADOR,
        username="op_existente",
        created_by=representante,
    )
    client = _token_client(representante)

    list_response = client.get(f"/api/comedores/{comedor_1.id}/usuarios/")
    assert list_response.status_code == 200
    assert list_response.data["count"] == 1
    assert list_response.data["results"][0]["id"] == operador_existente.id

    create_response = client.post(
        f"/api/comedores/{comedor_1.id}/usuarios/",
        {
            "username": "op_nuevo",
            "email": "op_nuevo@example.com",
            "password": "Secreta123!",
        },
        format="json",
    )
    assert create_response.status_code == 201
    assert create_response.data["username"] == "op_nuevo"
    assert create_response.data["rol"] == AccesoComedorPWA.ROL_OPERADOR


@pytest.mark.django_db
def test_operador_cannot_manage_users_endpoint(comedores):
    comedor_1, _ = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_creador",
    )
    operador = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_OPERADOR,
        username="op_solo",
        created_by=representante,
    )
    client = _token_client(operador)

    get_response = client.get(f"/api/comedores/{comedor_1.id}/usuarios/")
    post_response = client.post(
        f"/api/comedores/{comedor_1.id}/usuarios/",
        {"username": "otro", "email": "otro@example.com", "password": "Secreta123!"},
        format="json",
    )

    assert get_response.status_code == 403
    assert post_response.status_code == 403


@pytest.mark.django_db
def test_representante_can_deactivate_operador(comedores):
    comedor_1, _ = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_deact",
    )
    operador = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_OPERADOR,
        username="op_deact",
        created_by=representante,
    )
    client = _token_client(representante)

    response = client.patch(
        f"/api/comedores/{comedor_1.id}/usuarios/{operador.id}/desactivar/",
        {},
        format="json",
    )

    assert response.status_code == 200
    operador.refresh_from_db()
    acceso = AccesoComedorPWA.objects.get(user=operador, comedor=comedor_1)
    assert operador.is_active is False
    assert acceso.activo is False


@pytest.mark.django_db
def test_cualquier_representante_del_mismo_comedor_puede_desactivar(comedores):
    comedor_1, _ = comedores
    representante_1 = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_a",
    )
    representante_2 = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_b",
    )
    operador = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_OPERADOR,
        username="op_multi_rep",
        created_by=representante_1,
    )
    client = _token_client(representante_2)

    response = client.patch(
        f"/api/comedores/{comedor_1.id}/usuarios/{operador.id}/desactivar/",
        {},
        format="json",
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_nomina_scope_is_filtered_by_pwa_access(comedores):
    comedor_1, comedor_2 = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_nomina",
    )
    client = _token_client(representante)

    nomina_asignada = Nomina.objects.create(comedor=comedor_1)
    nomina_fuera_scope = Nomina.objects.create(comedor=comedor_2)

    ok_response = client.patch(
        f"/api/comedores/nomina/{nomina_asignada.id}/",
        {"estado": "activo"},
        format="json",
    )
    forbidden_scope_response = client.patch(
        f"/api/comedores/nomina/{nomina_fuera_scope.id}/",
        {"estado": "activo"},
        format="json",
    )

    assert ok_response.status_code == 200
    assert forbidden_scope_response.status_code == 404


@pytest.mark.django_db
def test_rendiciones_list_and_detail_by_scope(comedores):
    comedor_1, comedor_2 = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_rendiciones",
    )
    client = _token_client(representante)

    rendicion_1 = RendicionCuentaMensual.objects.create(
        comedor=comedor_1,
        mes=1,
        anio=2026,
        observaciones="Rendición enero",
    )
    RendicionCuentaMensual.objects.create(
        comedor=comedor_2,
        mes=2,
        anio=2026,
        observaciones="Rendición fuera de scope",
    )

    list_response = client.get(f"/api/comedores/{comedor_1.id}/rendiciones/")
    assert list_response.status_code == 200
    assert list_response.data["count"] == 1
    assert list_response.data["results"][0]["id"] == rendicion_1.id

    detail_response = client.get(
        f"/api/comedores/{comedor_1.id}/rendiciones/{rendicion_1.id}/"
    )
    assert detail_response.status_code == 200
    assert detail_response.data["id"] == rendicion_1.id

    forbidden_scope_response = client.get(
        f"/api/comedores/{comedor_2.id}/rendiciones/{rendicion_1.id}/"
    )
    assert forbidden_scope_response.status_code == 404


@pytest.mark.django_db
def test_adjuntar_y_presentar_rendicion(comedores, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    comedor_1, _ = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_adjuntar_rendicion",
    )
    client = _token_client(representante)

    rendicion = RendicionCuentaMensual.objects.create(
        comedor=comedor_1,
        mes=3,
        anio=2026,
    )

    present_without_docs_response = client.post(
        f"/api/comedores/{comedor_1.id}/rendiciones/{rendicion.id}/presentar/",
        {},
        format="json",
    )
    assert present_without_docs_response.status_code == 400

    archivo = SimpleUploadedFile(
        "comprobante_test.pdf",
        b"%PDF-1.4 test content",
        content_type="application/pdf",
    )
    upload_response = client.post(
        f"/api/comedores/{comedor_1.id}/rendiciones/{rendicion.id}/comprobantes/",
        {"archivo": archivo},
        format="multipart",
    )
    assert upload_response.status_code == 201
    assert len(upload_response.data["comprobantes"]) == 1

    present_response = client.post(
        f"/api/comedores/{comedor_1.id}/rendiciones/{rendicion.id}/presentar/",
        {},
        format="json",
    )
    assert present_response.status_code == 200
    rendicion.refresh_from_db()
    assert rendicion.documento_adjunto is True


@pytest.mark.django_db
def test_documentos_list_filter_and_download(comedores, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    comedor_1, comedor_2 = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_documentos",
    )
    client = _token_client(representante)

    comedor_1.foto_legajo = SimpleUploadedFile(
        "legajo_test.jpg",
        b"fake-jpeg-content",
        content_type="image/jpeg",
    )
    comedor_1.save(update_fields=["foto_legajo"])
    ImagenComedor.objects.create(
        comedor=comedor_1,
        imagen=SimpleUploadedFile(
            "imagen_test.jpg",
            b"fake-image-content",
            content_type="image/jpeg",
        ),
    )

    rendicion = RendicionCuentaMensual.objects.create(
        comedor=comedor_1,
        mes=4,
        anio=2026,
    )
    DocumentacionAdjunta.objects.create(
        nombre="Comprobante abril",
        archivo=SimpleUploadedFile(
            "comprobante_test.pdf",
            b"%PDF-1.4 fake content",
            content_type="application/pdf",
        ),
        rendicion_cuenta_mensual=rendicion,
    )

    list_response = client.get(f"/api/comedores/{comedor_1.id}/documentos/")
    assert list_response.status_code == 200
    assert list_response.data["count"] >= 3

    tipos = {item["tipo"] for item in list_response.data["results"]}
    assert "foto_legajo" in tipos
    assert "imagen_comedor" in tipos
    assert "documento_rendicion_mensual" in tipos

    by_type_response = client.get(
        f"/api/comedores/{comedor_1.id}/documentos/",
        {"tipo": "documento_rendicion_mensual"},
    )
    assert by_type_response.status_code == 200
    assert by_type_response.data["count"] == 1

    by_query_response = client.get(
        f"/api/comedores/{comedor_1.id}/documentos/",
        {"q": "comprobante_test"},
    )
    assert by_query_response.status_code == 200
    assert by_query_response.data["count"] == 1

    invalid_date_response = client.get(
        f"/api/comedores/{comedor_1.id}/documentos/",
        {"desde": "2026-13-01"},
    )
    assert invalid_date_response.status_code == 400

    documento_id = by_type_response.data["results"][0]["id"]
    download_response = client.get(
        f"/api/comedores/{comedor_1.id}/documentos/{documento_id}/download/"
    )
    assert download_response.status_code == 200
    assert "attachment" in download_response["Content-Disposition"]

    outside_scope_response = client.get(f"/api/comedores/{comedor_2.id}/documentos/")
    assert outside_scope_response.status_code == 404


@pytest.mark.django_db
def test_prestacion_alimentaria_returns_empty_payload_when_no_informes(comedores):
    comedor_1, _ = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_prestacion_empty",
    )
    client = _token_client(representante)

    response = client.get(f"/api/comedores/{comedor_1.id}/prestacion-alimentaria/")
    assert response.status_code == 200
    assert response.data["informe_id"] is None
    assert response.data["aprobadas_almuerzo_lunes"] is None


@pytest.mark.django_db
def test_prestacion_alimentaria_uses_latest_finalizado(comedores):
    comedor_1, _ = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_prestacion_latest",
    )
    client = _token_client(representante)

    admision = Admision.objects.create(comedor=comedor_1)
    informe_viejo = _create_informe_tecnico(
        admision,
        estado_formulario="finalizado",
        aprobadas_almuerzo_lunes=50,
    )
    informe_nuevo = _create_informe_tecnico(
        admision,
        estado_formulario="finalizado",
        aprobadas_almuerzo_lunes=120,
    )
    _create_informe_tecnico(
        admision,
        estado_formulario="borrador",
        aprobadas_almuerzo_lunes=999,
    )
    InformeTecnico.objects.filter(pk=informe_viejo.pk).update(
        modificado=date(2026, 1, 15)
    )
    InformeTecnico.objects.filter(pk=informe_nuevo.pk).update(
        modificado=date(2026, 2, 15)
    )

    response = client.get(f"/api/comedores/{comedor_1.id}/prestacion-alimentaria/")
    assert response.status_code == 200
    assert response.data["informe_id"] == informe_nuevo.id
    assert response.data["aprobadas_almuerzo_lunes"] == 120


@pytest.mark.django_db
def test_prestacion_alimentaria_historial_filters_by_period(comedores):
    comedor_1, _ = comedores
    representante = _create_pwa_user(
        comedor=comedor_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_prestacion_historial",
    )
    client = _token_client(representante)

    admision = Admision.objects.create(comedor=comedor_1)
    informe_enero = _create_informe_tecnico(admision, estado_formulario="finalizado")
    informe_febrero = _create_informe_tecnico(admision, estado_formulario="finalizado")
    informe_marzo = _create_informe_tecnico(admision, estado_formulario="finalizado")

    InformeTecnico.objects.filter(pk=informe_enero.pk).update(
        modificado=date(2026, 1, 20)
    )
    InformeTecnico.objects.filter(pk=informe_febrero.pk).update(
        modificado=date(2026, 2, 15)
    )
    InformeTecnico.objects.filter(pk=informe_marzo.pk).update(
        modificado=date(2026, 3, 10)
    )

    response = client.get(
        f"/api/comedores/{comedor_1.id}/prestacion-alimentaria/historial/",
        {"desde": "2026-02", "hasta": "2026-03"},
    )
    assert response.status_code == 200
    assert response.data["count"] == 2
    assert [item["informe_id"] for item in response.data["results"]] == [
        informe_marzo.id,
        informe_febrero.id,
    ]

    invalid_range_response = client.get(
        f"/api/comedores/{comedor_1.id}/prestacion-alimentaria/historial/",
        {"desde": "2026-05", "hasta": "2026-03"},
    )
    assert invalid_range_response.status_code == 400
