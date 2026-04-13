from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from comunicados.models import (
    Comunicado,
    ComunicadoAdjunto,
    EstadoComunicado,
    SubtipoComunicado,
    TipoComunicado,
)
from comedores.models import Comedor
from core.models import Provincia
from organizaciones.models import Organizacion
from pwa.models import AuditoriaOperacionPWA, LecturaMensajePWA
from rendicioncuentasmensual.models import DocumentacionAdjunta, RendicionCuentaMensual
from rendicioncuentasmensual.services import RendicionCuentaMensualService
from users.models import AccesoComedorPWA


@pytest.fixture
def espacios(db):
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    espacio_1 = Comedor.objects.create(
        nombre="Espacio Mensajes Uno", provincia=provincia
    )
    espacio_2 = Comedor.objects.create(
        nombre="Espacio Mensajes Dos", provincia=provincia
    )
    return espacio_1, espacio_2


def _create_pwa_user(*, comedor, role, username, password="testpass123"):
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
        activo=True,
    )
    return user


def _auth_client_for_user(user):
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


def _grant_mobile_rendicion_permission(user):
    permission = Permission.objects.get(
        content_type__app_label="rendicioncuentasmensual",
        codename="manage_mobile_rendicion",
    )
    user.user_permissions.add(permission)


def _create_comunicado(
    *, creador, titulo, para_todos_comedores=False, comedor=None, **overrides
):
    comunicado = Comunicado.objects.create(
        titulo=titulo,
        cuerpo=overrides.pop("cuerpo", "Contenido del mensaje"),
        estado=overrides.pop("estado", EstadoComunicado.PUBLICADO),
        tipo=overrides.pop("tipo", TipoComunicado.EXTERNO),
        subtipo=overrides.pop("subtipo", SubtipoComunicado.COMEDORES),
        para_todos_comedores=para_todos_comedores,
        fecha_publicacion=overrides.pop("fecha_publicacion", timezone.now()),
        fecha_vencimiento=overrides.pop("fecha_vencimiento", None),
        destacado=overrides.pop("destacado", False),
        usuario_creador=creador,
        usuario_ultima_modificacion=creador,
        **overrides,
    )
    if comedor is not None:
        comunicado.comedores.add(comedor)
    return comunicado


@pytest.mark.django_db
def test_list_mensajes_por_espacio_filtra_por_scope_y_estado(espacios):
    espacio_1, espacio_2 = espacios
    representante = _create_pwa_user(
        comedor=espacio_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_mensajes_list",
    )
    client = _auth_client_for_user(representante)

    _create_comunicado(
        creador=representante, titulo="Solo espacio 1", comedor=espacio_1
    )
    _create_comunicado(
        creador=representante, titulo="Para todos", para_todos_comedores=True
    )
    _create_comunicado(
        creador=representante, titulo="Solo espacio 2", comedor=espacio_2
    )
    _create_comunicado(
        creador=representante,
        titulo="Archivado",
        comedor=espacio_1,
        estado=EstadoComunicado.ARCHIVADO,
    )
    _create_comunicado(
        creador=representante,
        titulo="Vencido",
        comedor=espacio_1,
        fecha_vencimiento=timezone.now() - timedelta(days=1),
    )

    response = client.get(f"/api/pwa/espacios/{espacio_1.id}/mensajes/")

    assert response.status_code == 200
    assert response.data["count"] == 2
    assert response.data["unread_count"] == 2
    titulos = [item["titulo"] for item in response.data["results"]]
    assert "Solo espacio 1" in titulos
    assert "Para todos" in titulos
    assert "Solo espacio 2" not in titulos
    assert all(item["visto"] is False for item in response.data["results"])
    assert response.data["unread_general_count"] == 0
    assert response.data["unread_espacio_count"] == 2


@pytest.mark.django_db
def test_list_mensajes_por_espacio_incluye_notificaciones_generales(espacios):
    espacio_1, _ = espacios
    representante = _create_pwa_user(
        comedor=espacio_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_mensajes_generales",
    )
    client = _auth_client_for_user(representante)

    _create_comunicado(
        creador=representante,
        titulo="General Mobile",
        subtipo=SubtipoComunicado.INSTITUCIONAL,
    )
    _create_comunicado(
        creador=representante,
        titulo="Para el espacio",
        comedor=espacio_1,
        subtipo=SubtipoComunicado.COMEDORES,
    )

    response = client.get(f"/api/pwa/espacios/{espacio_1.id}/mensajes/")

    assert response.status_code == 200
    assert response.data["count"] == 2
    assert response.data["unread_general_count"] == 1
    assert response.data["unread_espacio_count"] == 1
    assert len(response.data["secciones"]["generales"]) == 1
    assert response.data["secciones"]["generales"][0]["titulo"] == "General Mobile"
    assert response.data["secciones"]["generales"][0]["seccion"] == "general"
    assert len(response.data["secciones"]["espacios"]) == 1
    assert response.data["secciones"]["espacios"][0]["titulo"] == "Para el espacio"
    assert response.data["secciones"]["espacios"][0]["seccion"] == "espacio"


@pytest.mark.django_db
def test_list_mensajes_por_espacio_incluye_contadores_agrupados_para_rendiciones(
    espacios,
):
    espacio_1, _ = espacios
    representante = _create_pwa_user(
        comedor=espacio_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_mensajes_grouped_counts",
    )
    _grant_mobile_rendicion_permission(representante)
    client = _auth_client_for_user(representante)

    _create_comunicado(
        creador=representante,
        titulo="Comunicado del espacio",
        comedor=espacio_1,
        subtipo=SubtipoComunicado.COMEDORES,
    )
    rendicion = RendicionCuentaMensual.objects.create(
        comedor=espacio_1,
        mes=4,
        anio=2026,
        convenio="Convenio grouped",
        numero_rendicion=3,
        periodo_inicio=timezone.now().date(),
        periodo_fin=timezone.now().date(),
        estado=RendicionCuentaMensual.ESTADO_REVISION,
    )
    documento_1 = DocumentacionAdjunta.objects.create(
        nombre="comprobante-1.pdf",
        categoria=DocumentacionAdjunta.CATEGORIA_COMPROBANTES,
        estado=DocumentacionAdjunta.ESTADO_PRESENTADO,
        rendicion_cuenta_mensual=rendicion,
        archivo=SimpleUploadedFile(
            "comprobante-1.pdf",
            b"pdf-1",
            content_type="application/pdf",
        ),
    )
    documento_2 = DocumentacionAdjunta.objects.create(
        nombre="comprobante-2.pdf",
        categoria=DocumentacionAdjunta.CATEGORIA_COMPROBANTES,
        estado=DocumentacionAdjunta.ESTADO_PRESENTADO,
        rendicion_cuenta_mensual=rendicion,
        archivo=SimpleUploadedFile(
            "comprobante-2.pdf",
            b"pdf-2",
            content_type="application/pdf",
        ),
    )

    RendicionCuentaMensualService.actualizar_estado_documento_revision(
        documento=documento_1,
        estado=DocumentacionAdjunta.ESTADO_SUBSANAR,
        observaciones="Observacion 1",
        actor=representante,
    )
    RendicionCuentaMensualService.actualizar_estado_documento_revision(
        documento=documento_2,
        estado=DocumentacionAdjunta.ESTADO_SUBSANAR,
        observaciones="Observacion 2",
        actor=representante,
    )

    response = client.get(f"/api/pwa/espacios/{espacio_1.id}/mensajes/")

    assert response.status_code == 200
    assert response.data["unread_count"] == 2
    assert response.data["unread_espacio_count"] == 2
    assert response.data["unread_grouped_count"] == 2
    assert response.data["unread_espacio_non_rendicion_count"] == 1
    assert response.data["unread_general_ids"] == []
    assert response.data["unread_rendicion_ids"] == [rendicion.id]


@pytest.mark.django_db
def test_revision_de_rendicion_genera_mensaje_mobile_visible_en_el_espacio(espacios):
    espacio_1, espacio_2 = espacios
    organizacion = Organizacion.objects.create(nombre="Organizacion Rendicion")
    espacio_1.organizacion = organizacion
    espacio_1.codigo_de_proyecto = "PROY-55"
    espacio_1.save(update_fields=["organizacion", "codigo_de_proyecto"])
    espacio_2.organizacion = organizacion
    espacio_2.codigo_de_proyecto = "PROY-55"
    espacio_2.save(update_fields=["organizacion", "codigo_de_proyecto"])
    representante = _create_pwa_user(
        comedor=espacio_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_rendicion_notif",
    )
    AccesoComedorPWA.objects.create(
        user=representante,
        comedor=espacio_2,
        rol=AccesoComedorPWA.ROL_REPRESENTANTE,
        activo=True,
    )
    _grant_mobile_rendicion_permission(representante)
    client = _auth_client_for_user(representante)
    rendicion = RendicionCuentaMensual.objects.create(
        comedor=espacio_1,
        mes=4,
        anio=2026,
        convenio="Convenio test",
        numero_rendicion=55,
        periodo_inicio=timezone.now().date(),
        periodo_fin=timezone.now().date(),
        estado=RendicionCuentaMensual.ESTADO_REVISION,
    )
    documento = DocumentacionAdjunta.objects.create(
        nombre="comprobante.pdf",
        categoria=DocumentacionAdjunta.CATEGORIA_COMPROBANTES,
        estado=DocumentacionAdjunta.ESTADO_PRESENTADO,
        rendicion_cuenta_mensual=rendicion,
        archivo=SimpleUploadedFile(
            "comprobante.pdf", b"pdf", content_type="application/pdf"
        ),
    )

    RendicionCuentaMensualService.actualizar_estado_documento_revision(
        documento=documento,
        estado=DocumentacionAdjunta.ESTADO_SUBSANAR,
        observaciones="Volver a subir el documento completo",
        actor=representante,
    )

    response = client.get(f"/api/pwa/espacios/{espacio_2.id}/mensajes/")

    assert response.status_code == 200
    titulos = [item["titulo"] for item in response.data["results"]]
    expected_title_prefix = "Proyecto PROY-55 | Convenio Convenio test |"
    assert any(
        item.startswith(expected_title_prefix) and "documento a subsanar" in item
        for item in titulos
    )
    mensaje = next(
        item
        for item in response.data["results"]
        if item["titulo"].startswith(expected_title_prefix)
        and "documento a subsanar" in item["titulo"]
    )

    detail_response = client.get(
        f"/api/pwa/espacios/{espacio_2.id}/mensajes/{mensaje['id']}/"
    )
    assert detail_response.status_code == 200
    assert "Proyecto: PROY-55." in detail_response.data["cuerpo"]
    assert "Convenio: Convenio test." in detail_response.data["cuerpo"]
    assert (
        "Observaciones: Volver a subir el documento completo."
        in detail_response.data["cuerpo"]
    )
    assert "[SISOC_ACCION]" not in detail_response.data["cuerpo"]
    assert detail_response.data["accion"] == {
        "tipo": "rendicion_detalle",
        "rendicion_id": rendicion.id,
    }


@pytest.mark.django_db
def test_mensaje_de_rendicion_se_oculta_si_el_usuario_no_tiene_permiso_mobile_rendicion(
    espacios,
):
    espacio_1, espacio_2 = espacios
    organizacion = Organizacion.objects.create(nombre="Organizacion Rendicion Permisos")
    espacio_1.organizacion = organizacion
    espacio_1.codigo_de_proyecto = "PROY-88"
    espacio_1.save(update_fields=["organizacion", "codigo_de_proyecto"])
    espacio_2.organizacion = organizacion
    espacio_2.codigo_de_proyecto = "PROY-88"
    espacio_2.save(update_fields=["organizacion", "codigo_de_proyecto"])

    creador = _create_pwa_user(
        comedor=espacio_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_rendicion_perm_ok",
    )
    _grant_mobile_rendicion_permission(creador)
    usuario_sin_permiso = _create_pwa_user(
        comedor=espacio_2,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_rendicion_perm_no",
    )
    client = _auth_client_for_user(usuario_sin_permiso)

    rendicion = RendicionCuentaMensual.objects.create(
        comedor=espacio_1,
        mes=4,
        anio=2026,
        numero_rendicion=88,
        periodo_inicio=timezone.now().date(),
        periodo_fin=timezone.now().date(),
        estado=RendicionCuentaMensual.ESTADO_REVISION,
    )
    documento = DocumentacionAdjunta.objects.create(
        nombre="comprobante.pdf",
        categoria=DocumentacionAdjunta.CATEGORIA_COMPROBANTES,
        estado=DocumentacionAdjunta.ESTADO_PRESENTADO,
        rendicion_cuenta_mensual=rendicion,
        archivo=SimpleUploadedFile(
            "comprobante.pdf", b"pdf", content_type="application/pdf"
        ),
    )

    RendicionCuentaMensualService.actualizar_estado_documento_revision(
        documento=documento,
        estado=DocumentacionAdjunta.ESTADO_SUBSANAR,
        observaciones="Corregir archivo",
        actor=creador,
    )

    response = client.get(f"/api/pwa/espacios/{espacio_2.id}/mensajes/")

    assert response.status_code == 200
    titulos = [item["titulo"] for item in response.data["results"]]
    assert "Rendición 88: documento a subsanar" not in titulos


@pytest.mark.django_db
def test_mensaje_de_rendicion_se_oculta_si_el_usuario_no_esta_en_el_scope_de_la_rendicion(
    espacios,
):
    espacio_1, espacio_2 = espacios
    organizacion = Organizacion.objects.create(nombre="Organizacion Scope Rendicion")
    espacio_1.organizacion = organizacion
    espacio_1.codigo_de_proyecto = "PROY-99"
    espacio_1.save(update_fields=["organizacion", "codigo_de_proyecto"])
    espacio_2.organizacion = organizacion
    espacio_2.codigo_de_proyecto = "PROY-OTRO"
    espacio_2.save(update_fields=["organizacion", "codigo_de_proyecto"])

    creador = _create_pwa_user(
        comedor=espacio_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_rendicion_scope_ok",
    )
    _grant_mobile_rendicion_permission(creador)

    usuario_otro_scope = _create_pwa_user(
        comedor=espacio_2,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_rendicion_scope_no",
    )
    _grant_mobile_rendicion_permission(usuario_otro_scope)
    client = _auth_client_for_user(usuario_otro_scope)

    rendicion = RendicionCuentaMensual.objects.create(
        comedor=espacio_1,
        mes=4,
        anio=2026,
        numero_rendicion=99,
        periodo_inicio=timezone.now().date(),
        periodo_fin=timezone.now().date(),
        estado=RendicionCuentaMensual.ESTADO_REVISION,
    )
    documento = DocumentacionAdjunta.objects.create(
        nombre="comprobante.pdf",
        categoria=DocumentacionAdjunta.CATEGORIA_COMPROBANTES,
        estado=DocumentacionAdjunta.ESTADO_PRESENTADO,
        rendicion_cuenta_mensual=rendicion,
        archivo=SimpleUploadedFile(
            "comprobante.pdf", b"pdf", content_type="application/pdf"
        ),
    )

    RendicionCuentaMensualService.actualizar_estado_documento_revision(
        documento=documento,
        estado=DocumentacionAdjunta.ESTADO_SUBSANAR,
        observaciones="Corregir archivo",
        actor=creador,
    )

    response = client.get(f"/api/pwa/espacios/{espacio_2.id}/mensajes/")

    assert response.status_code == 200
    titulos = [item["titulo"] for item in response.data["results"]]
    assert "Rendición 99: documento a subsanar" not in titulos


@pytest.mark.django_db
def test_mensaje_de_rendicion_se_archiva_cuando_la_subsanacion_se_reenvia(
    espacios, settings, tmp_path
):
    settings.MEDIA_ROOT = str(tmp_path)
    espacio_1, espacio_2 = espacios
    organizacion = Organizacion.objects.create(nombre="Organizacion Rendicion Archivo")
    espacio_1.organizacion = organizacion
    espacio_1.codigo_de_proyecto = "PROY-66"
    espacio_1.save(update_fields=["organizacion", "codigo_de_proyecto"])
    espacio_2.organizacion = organizacion
    espacio_2.codigo_de_proyecto = "PROY-66"
    espacio_2.save(update_fields=["organizacion", "codigo_de_proyecto"])

    representante = _create_pwa_user(
        comedor=espacio_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_rendicion_archiva",
    )
    _grant_mobile_rendicion_permission(representante)
    client = _auth_client_for_user(representante)

    rendicion = RendicionCuentaMensual.objects.create(
        comedor=espacio_1,
        mes=4,
        anio=2026,
        convenio="Convenio test",
        numero_rendicion=66,
        periodo_inicio=timezone.now().date(),
        periodo_fin=timezone.now().date(),
        estado=RendicionCuentaMensual.ESTADO_SUBSANAR,
    )
    for categoria in (
        DocumentacionAdjunta.CATEGORIA_FORMULARIO_II,
        DocumentacionAdjunta.CATEGORIA_FORMULARIO_III,
        DocumentacionAdjunta.CATEGORIA_FORMULARIO_V,
        DocumentacionAdjunta.CATEGORIA_EXTRACTO_BANCARIO,
    ):
        DocumentacionAdjunta.objects.create(
            nombre=f"{categoria}.pdf",
            categoria=categoria,
            estado=DocumentacionAdjunta.ESTADO_VALIDADO,
            rendicion_cuenta_mensual=rendicion,
            archivo=SimpleUploadedFile(
                f"{categoria}.pdf",
                b"pdf",
                content_type="application/pdf",
            ),
        )
    observado = DocumentacionAdjunta.objects.create(
        nombre="comprobante.pdf",
        categoria=DocumentacionAdjunta.CATEGORIA_COMPROBANTES,
        estado=DocumentacionAdjunta.ESTADO_SUBSANAR,
        observaciones="Volver a subir el documento completo",
        rendicion_cuenta_mensual=rendicion,
        archivo=SimpleUploadedFile(
            "comprobante.pdf", b"pdf", content_type="application/pdf"
        ),
    )

    RendicionCuentaMensualService._crear_notificacion_mobile_revision_documento(
        documento=observado,
        actor=representante,
    )

    previo = client.get(f"/api/pwa/espacios/{espacio_1.id}/mensajes/")
    assert previo.status_code == 200
    assert any(
        item["accion"] == {"tipo": "rendicion_detalle", "rendicion_id": rendicion.id}
        for item in previo.data["results"]
    )

    RendicionCuentaMensualService.adjuntar_documentacion_mobile(
        rendicion=rendicion,
        categoria=DocumentacionAdjunta.CATEGORIA_COMPROBANTES,
        documento_data={
            "archivo": SimpleUploadedFile(
                "comprobante-nuevo.pdf",
                b"pdf nuevo",
                content_type="application/pdf",
            ),
            "nombre": "comprobante-nuevo.pdf",
        },
        actor=representante,
        documento_subsanado_id=observado.id,
    )
    RendicionCuentaMensualService.presentar_rendicion_mobile(
        rendicion,
        actor=representante,
    )

    posterior = client.get(f"/api/pwa/espacios/{espacio_1.id}/mensajes/")
    assert posterior.status_code == 200
    assert not any(
        item["accion"] == {"tipo": "rendicion_detalle", "rendicion_id": rendicion.id}
        for item in posterior.data["results"]
    )


@pytest.mark.django_db
def test_operador_pwa_tambien_puede_listar_mensajes(espacios):
    espacio_1, _ = espacios
    user_model = get_user_model()
    creador = user_model.objects.create_user(
        username="creador_mensajes",
        email="creador_mensajes@example.com",
        password="testpass123",
    )
    operador = _create_pwa_user(
        comedor=espacio_1,
        role=AccesoComedorPWA.ROL_OPERADOR,
        username="operador_mensajes",
    )
    client = _auth_client_for_user(operador)
    _create_comunicado(creador=creador, titulo="Mensaje operador", comedor=espacio_1)

    response = client.get(f"/api/pwa/espacios/{espacio_1.id}/mensajes/")

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["titulo"] == "Mensaje operador"


@pytest.mark.django_db
def test_mensajes_fuera_de_scope_retorna_404(espacios):
    espacio_1, espacio_2 = espacios
    representante = _create_pwa_user(
        comedor=espacio_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_scope_mensajes",
    )
    client = _auth_client_for_user(representante)

    response = client.get(f"/api/pwa/espacios/{espacio_2.id}/mensajes/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_marcar_mensaje_como_visto_persiste_lectura_y_auditoria(espacios):
    espacio_1, _ = espacios
    representante = _create_pwa_user(
        comedor=espacio_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_mark_seen",
    )
    client = _auth_client_for_user(representante)
    mensaje = _create_comunicado(
        creador=representante,
        titulo="Mensaje a leer",
        comedor=espacio_1,
    )

    response = client.patch(
        f"/api/pwa/espacios/{espacio_1.id}/mensajes/{mensaje.id}/marcar-visto/",
        {},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["id"] == mensaje.id
    assert response.data["visto"] is True
    lectura = LecturaMensajePWA.objects.get(
        comunicado=mensaje,
        comedor=espacio_1,
        user=representante,
    )
    assert lectura.visto is True
    assert lectura.fecha_visto is not None
    assert AuditoriaOperacionPWA.objects.filter(
        entidad="mensaje_lectura",
        entidad_id=lectura.id,
        accion="create",
    ).exists()


@pytest.mark.django_db
def test_marcar_mensaje_como_visto_es_idempotente(espacios):
    espacio_1, _ = espacios
    representante = _create_pwa_user(
        comedor=espacio_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_seen_idempotente",
    )
    client = _auth_client_for_user(representante)
    mensaje = _create_comunicado(
        creador=representante,
        titulo="Mensaje idempotente",
        comedor=espacio_1,
    )

    first_response = client.patch(
        f"/api/pwa/espacios/{espacio_1.id}/mensajes/{mensaje.id}/marcar-visto/",
        {},
        format="json",
    )
    second_response = client.patch(
        f"/api/pwa/espacios/{espacio_1.id}/mensajes/{mensaje.id}/marcar-visto/",
        {},
        format="json",
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert (
        LecturaMensajePWA.objects.filter(
            comunicado=mensaje,
            comedor=espacio_1,
            user=representante,
        ).count()
        == 1
    )
    assert AuditoriaOperacionPWA.objects.filter(entidad="mensaje_lectura").count() == 1


@pytest.mark.django_db
def test_mensaje_general_marcado_visto_se_refleja_en_todos_los_espacios_del_usuario(
    espacios,
):
    espacio_1, espacio_2 = espacios
    representante = _create_pwa_user(
        comedor=espacio_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_seen_general",
    )
    AccesoComedorPWA.objects.create(
        user=representante,
        comedor=espacio_2,
        rol=AccesoComedorPWA.ROL_REPRESENTANTE,
        activo=True,
    )
    client = _auth_client_for_user(representante)
    mensaje = _create_comunicado(
        creador=representante,
        titulo="General todos",
        subtipo=SubtipoComunicado.INSTITUCIONAL,
    )

    mark_response = client.patch(
        f"/api/pwa/espacios/{espacio_1.id}/mensajes/{mensaje.id}/marcar-visto/",
        {},
        format="json",
    )
    list_response_space_2 = client.get(f"/api/pwa/espacios/{espacio_2.id}/mensajes/")

    assert mark_response.status_code == 200
    assert list_response_space_2.status_code == 200
    assert list_response_space_2.data["unread_general_count"] == 0
    assert list_response_space_2.data["results"][0]["visto"] is True
    assert (
        LecturaMensajePWA.objects.filter(
            comunicado=mensaje,
            user=representante,
        ).count()
        == 2
    )


@pytest.mark.django_db
def test_detalle_y_listado_reflejan_estado_visto(espacios):
    espacio_1, _ = espacios
    representante = _create_pwa_user(
        comedor=espacio_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_seen_state",
    )
    client = _auth_client_for_user(representante)
    mensaje = _create_comunicado(
        creador=representante,
        titulo="Mensaje detalle",
        comedor=espacio_1,
    )
    LecturaMensajePWA.objects.create(
        comunicado=mensaje,
        comedor=espacio_1,
        user=representante,
        visto=True,
        fecha_visto=timezone.now(),
    )

    detail_response = client.get(
        f"/api/pwa/espacios/{espacio_1.id}/mensajes/{mensaje.id}/"
    )
    list_response = client.get(f"/api/pwa/espacios/{espacio_1.id}/mensajes/")

    assert detail_response.status_code == 200
    assert detail_response.data["visto"] is True
    assert detail_response.data["fecha_visto"] is not None
    assert list_response.status_code == 200
    assert list_response.data["unread_count"] == 0
    assert list_response.data["results"][0]["visto"] is True


@pytest.mark.django_db
@override_settings(ROOT_URLCONF="tests.test_urls_pr1400_fixes")
def test_list_mensajes_keeps_global_unread_counters_with_pagination(espacios):
    espacio_1, _ = espacios
    representante = _create_pwa_user(
        comedor=espacio_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_mensajes_paginados",
    )
    client = _auth_client_for_user(representante)

    general = _create_comunicado(
        creador=representante,
        titulo="General leido",
        subtipo=SubtipoComunicado.INSTITUCIONAL,
    )
    for index in range(21):
        _create_comunicado(
            creador=representante,
            titulo=f"Mensaje paginado {index}",
            comedor=espacio_1,
            fecha_publicacion=timezone.now() + timedelta(minutes=index + 1),
        )
    LecturaMensajePWA.objects.create(
        comunicado=general,
        comedor=espacio_1,
        user=representante,
        visto=True,
        fecha_visto=timezone.now(),
    )

    response = client.get(f"/api/pwa/espacios/{espacio_1.id}/mensajes/", {"page": 2})

    assert response.status_code == 200
    assert response.data["count"] == 22
    assert response.data["current_page"] == 2
    assert len(response.data["results"]) == 2
    assert response.data["unread_count"] == 21
    assert response.data["unread_general_count"] == 0
    assert response.data["unread_espacio_count"] == 21


@pytest.mark.django_db
def test_detalle_mensaje_incluye_fecha_creacion_y_datos_de_adjuntos(
    espacios, settings, tmp_path
):
    settings.MEDIA_ROOT = str(tmp_path)
    espacio_1, _ = espacios
    representante = _create_pwa_user(
        comedor=espacio_1,
        role=AccesoComedorPWA.ROL_REPRESENTANTE,
        username="rep_detail_adjuntos",
    )
    client = _auth_client_for_user(representante)
    mensaje = _create_comunicado(
        creador=representante,
        titulo="Mensaje con adjunto",
        comedor=espacio_1,
    )
    adjunto = ComunicadoAdjunto.objects.create(
        comunicado=mensaje,
        archivo=SimpleUploadedFile(
            "archivo.pdf",
            b"%PDF-1.4 fake content",
            content_type="application/pdf",
        ),
    )

    response = client.get(f"/api/pwa/espacios/{espacio_1.id}/mensajes/{mensaje.id}/")

    assert response.status_code == 200
    assert response.data["fecha_creacion"] is not None
    assert response.data["adjuntos"][0]["nombre_original"] == adjunto.nombre_original
    assert response.data["adjuntos"][0]["fecha_subida"] is not None
    assert response.data["adjuntos"][0]["url"] is not None
