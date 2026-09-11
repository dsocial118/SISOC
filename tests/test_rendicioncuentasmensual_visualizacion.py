from io import BytesIO
from datetime import timedelta

from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils import timezone
import pytest

from rendicioncuentasmensual.models import (
    DocumentacionAdjunta,
    RendicionCuentaMensual,
)
from rendicioncuentasmensual.services import (
    RendicionCuentaMensualService,
    RendicionProcesoService,
)


@pytest.fixture(autouse=True)
def global_temp_media_root():
    """Evita depender de temporales del sistema en este archivo focalizado."""


def _otorgar_permiso(usuario, codename):
    usuario.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="rendicioncuentasmensual",
            codename=codename,
        )
    )


def _crear_rendicion(etapa=RendicionCuentaMensual.ETAPA_REVISION_DOCUMENTACION):
    return RendicionCuentaMensual.objects.create(
        mes=9,
        anio=2026,
        etapa_proceso=etapa,
        subestado_proceso=RendicionCuentaMensual.SUBESTADO_EN_CURSO,
        estado=RendicionCuentaMensual.ESTADO_REVISION,
    )


def _crear_documento(rendicion, nombre="Comprobante.pdf", **kwargs):
    return DocumentacionAdjunta.objects.create(
        nombre=nombre,
        archivo=f"documentos/{nombre}",
        rendicion_cuenta_mensual=rendicion,
        **kwargs,
    )


def _url_documento(documento):
    return reverse("rendicioncuentasmensual_documento_ver", kwargs={"pk": documento.pk})


@pytest.mark.django_db
def test_visualizacion_por_usuario_de_etapa_vigente_confirma_documento(
    client, django_user_model, mocker
):
    rendicion = _crear_rendicion()
    documento = _crear_documento(rendicion)
    mocker.patch(
        "django.db.models.fields.files.FieldFile.open",
        return_value=BytesIO(b"contenido"),
    )
    usuario = django_user_model.objects.create_user(username="territorial")
    _otorgar_permiso(usuario, "manage_territorial_stage")
    client.force_login(usuario)

    response = client.get(_url_documento(documento))

    assert response.status_code == 200
    response.close()
    documento.refresh_from_db()
    assert documento.visualizacion_etapa == rendicion.etapa_proceso
    assert documento.visualizacion_usuario == usuario
    assert documento.visualizacion_fecha is not None


@pytest.mark.django_db
def test_usuario_sin_permisos_de_acceso_no_ve_ni_confirma(
    client, django_user_model, mocker
):
    rendicion = _crear_rendicion()
    documento = _crear_documento(rendicion)
    abrir = mocker.patch(
        "django.db.models.fields.files.FieldFile.open",
        return_value=BytesIO(b"contenido"),
    )
    usuario = django_user_model.objects.create_user(username="sin-permisos")
    client.force_login(usuario)

    response = client.get(_url_documento(documento))

    assert response.status_code == 403
    abrir.assert_not_called()
    documento.refresh_from_db()
    assert documento.visualizacion_etapa is None
    assert documento.visualizacion_usuario is None
    assert documento.visualizacion_fecha is None


@pytest.mark.django_db
def test_permiso_de_otra_etapa_permite_ver_pero_no_confirma(
    client, django_user_model, mocker
):
    rendicion = _crear_rendicion(RendicionCuentaMensual.ETAPA_AUDITORIA)
    documento = _crear_documento(rendicion)
    mocker.patch(
        "django.db.models.fields.files.FieldFile.open",
        return_value=BytesIO(b"contenido"),
    )
    usuario = django_user_model.objects.create_user(username="territorial-otra-etapa")
    _otorgar_permiso(usuario, "manage_territorial_stage")
    client.force_login(usuario)

    response = client.get(_url_documento(documento))

    assert response.status_code == 200
    response.close()
    documento.refresh_from_db()
    assert documento.visualizacion_etapa is None
    assert documento.visualizacion_usuario is None
    assert documento.visualizacion_fecha is None


@pytest.mark.django_db
def test_archivo_inexistente_retorna_404_sin_confirmar(
    client, django_user_model, mocker
):
    rendicion = _crear_rendicion()
    documento = _crear_documento(rendicion)
    mocker.patch(
        "django.db.models.fields.files.FieldFile.open",
        side_effect=FileNotFoundError,
    )
    usuario = django_user_model.objects.create_user(username="territorial-sin-archivo")
    _otorgar_permiso(usuario, "manage_territorial_stage")
    client.force_login(usuario)

    response = client.get(_url_documento(documento))

    assert response.status_code == 404
    documento.refresh_from_db()
    assert documento.visualizacion_etapa is None
    assert documento.visualizacion_usuario is None
    assert documento.visualizacion_fecha is None


@pytest.mark.django_db
def test_segunda_visualizacion_pisa_usuario_y_fecha(client, django_user_model, mocker):
    rendicion = _crear_rendicion()
    documento = _crear_documento(rendicion)
    mocker.patch(
        "django.db.models.fields.files.FieldFile.open",
        side_effect=lambda *_args, **_kwargs: BytesIO(b"contenido"),
    )
    primer_usuario = django_user_model.objects.create_user(username="territorial-uno")
    segundo_usuario = django_user_model.objects.create_user(username="territorial-dos")
    _otorgar_permiso(primer_usuario, "manage_territorial_stage")
    _otorgar_permiso(segundo_usuario, "manage_territorial_stage")

    client.force_login(primer_usuario)
    primera_respuesta = client.get(_url_documento(documento))
    assert primera_respuesta.status_code == 200
    primera_respuesta.close()
    primera_fecha = timezone.now() - timedelta(hours=1)
    DocumentacionAdjunta.objects.filter(pk=documento.pk).update(
        visualizacion_fecha=primera_fecha
    )

    client.force_login(segundo_usuario)
    segunda_respuesta = client.get(_url_documento(documento))
    assert segunda_respuesta.status_code == 200
    segunda_respuesta.close()

    documento.refresh_from_db()
    assert documento.visualizacion_usuario == segundo_usuario
    assert documento.visualizacion_fecha > primera_fecha


@pytest.mark.django_db
def test_validar_documento_no_cambia_confirmacion(django_user_model):
    rendicion = _crear_rendicion()
    usuario = django_user_model.objects.create_user(username="revisor-validacion")
    fecha = timezone.now()
    documento = _crear_documento(
        rendicion,
        visualizacion_etapa=rendicion.etapa_proceso,
        visualizacion_usuario=usuario,
        visualizacion_fecha=fecha,
    )

    RendicionCuentaMensualService.actualizar_estado_documento_revision(
        documento=documento,
        estado=DocumentacionAdjunta.ESTADO_VALIDADO,
        actor=usuario,
    )

    documento.refresh_from_db()
    assert documento.visualizacion_etapa == rendicion.etapa_proceso
    assert documento.visualizacion_usuario == usuario
    assert documento.visualizacion_fecha == fecha


@pytest.mark.django_db
def test_enviar_documento_a_subsanar_no_cambia_confirmacion(django_user_model):
    rendicion = _crear_rendicion()
    usuario = django_user_model.objects.create_user(username="revisor-subsanacion")
    fecha = timezone.now()
    documento = _crear_documento(
        rendicion,
        visualizacion_etapa=rendicion.etapa_proceso,
        visualizacion_usuario=usuario,
        visualizacion_fecha=fecha,
    )

    RendicionCuentaMensualService.actualizar_estado_documento_revision(
        documento=documento,
        estado=DocumentacionAdjunta.ESTADO_SUBSANAR,
        observaciones="El documento no es legible.",
        actor=usuario,
    )

    documento.refresh_from_db()
    assert documento.visualizacion_etapa == rendicion.etapa_proceso
    assert documento.visualizacion_usuario == usuario
    assert documento.visualizacion_fecha == fecha


@pytest.mark.django_db
def test_reemplazo_subsanado_resetea_solo_documento_reemplazado(django_user_model):
    rendicion = _crear_rendicion()
    rendicion.estado = RendicionCuentaMensual.ESTADO_SUBSANAR
    rendicion.subestado_proceso = (
        RendicionCuentaMensual.SUBESTADO_PENDIENTE_CORRECCIONES
    )
    rendicion.save(update_fields=["estado", "subestado_proceso"])
    usuario = django_user_model.objects.create_user(username="revisor-reemplazo")
    fecha = timezone.now()
    reemplazado = _crear_documento(
        rendicion,
        estado=DocumentacionAdjunta.ESTADO_SUBSANAR,
        visualizacion_etapa=rendicion.etapa_proceso,
        visualizacion_usuario=usuario,
        visualizacion_fecha=fecha,
    )
    otro = _crear_documento(
        rendicion,
        nombre="Otro.pdf",
        categoria=DocumentacionAdjunta.CATEGORIA_OTROS,
        estado=DocumentacionAdjunta.ESTADO_SUBSANAR,
        visualizacion_etapa=rendicion.etapa_proceso,
        visualizacion_usuario=usuario,
        visualizacion_fecha=fecha,
    )

    nuevo = RendicionCuentaMensualService.adjuntar_documentacion_mobile(
        rendicion=rendicion,
        categoria=reemplazado.categoria,
        documento_data={
            "nombre": "Reemplazo.pdf",
            "archivo": "documentos/reemplazo.pdf",
        },
        actor=usuario,
        documento_subsanado_id=reemplazado.pk,
    )

    reemplazado.refresh_from_db()
    otro.refresh_from_db()
    nuevo.refresh_from_db()
    assert reemplazado.visualizacion_etapa is None
    assert reemplazado.visualizacion_usuario is None
    assert reemplazado.visualizacion_fecha is None
    assert otro.visualizacion_etapa == rendicion.etapa_proceso
    assert otro.visualizacion_usuario == usuario
    assert otro.visualizacion_fecha == fecha
    assert nuevo.visualizacion_etapa is None
    assert nuevo.visualizacion_usuario is None
    assert nuevo.visualizacion_fecha is None


@pytest.mark.django_db
def test_avance_de_etapa_resetea_todas_las_confirmaciones_incluso_validadas(
    django_user_model,
):
    rendicion = _crear_rendicion()
    usuario = django_user_model.objects.create_user(username="revisor-avance")
    fecha = timezone.now()
    documentos = [
        _crear_documento(
            rendicion,
            nombre=f"Documento-{indice}.pdf",
            estado=DocumentacionAdjunta.ESTADO_VALIDADO,
            visualizacion_etapa=rendicion.etapa_proceso,
            visualizacion_usuario=usuario,
            visualizacion_fecha=fecha,
        )
        for indice in range(2)
    ]

    RendicionProcesoService.ejecutar(
        rendicion=rendicion,
        accion=RendicionProcesoService.ACCION_FINALIZAR_TERRITORIAL,
        datos={},
        actor=usuario,
    )

    rendicion.refresh_from_db()
    assert rendicion.etapa_proceso == RendicionCuentaMensual.ETAPA_REVISION_AUDITORIA
    for documento in documentos:
        documento.refresh_from_db()
        assert documento.estado == DocumentacionAdjunta.ESTADO_VALIDADO
        assert documento.visualizacion_etapa is None
        assert documento.visualizacion_usuario is None
        assert documento.visualizacion_fecha is None


@pytest.mark.django_db(transaction=True)
def test_falla_del_avance_revierte_reset_de_confirmaciones(django_user_model, mocker):
    rendicion = _crear_rendicion()
    usuario = django_user_model.objects.create_user(username="revisor-rollback")
    fecha = timezone.now()
    documento = _crear_documento(
        rendicion,
        estado=DocumentacionAdjunta.ESTADO_VALIDADO,
        visualizacion_etapa=rendicion.etapa_proceso,
        visualizacion_usuario=usuario,
        visualizacion_fecha=fecha,
    )
    mocker.patch.object(rendicion, "save", side_effect=RuntimeError("Falló el avance"))

    with pytest.raises(RuntimeError, match="Falló el avance"):
        RendicionProcesoService.ejecutar(
            rendicion=rendicion,
            accion=RendicionProcesoService.ACCION_FINALIZAR_TERRITORIAL,
            datos={},
            actor=usuario,
        )

    documento.refresh_from_db()
    assert documento.visualizacion_etapa == (
        RendicionCuentaMensual.ETAPA_REVISION_DOCUMENTACION
    )
    assert documento.visualizacion_usuario == usuario
    assert documento.visualizacion_fecha == fecha


@pytest.mark.django_db
def test_confirmar_en_una_rendicion_no_afecta_documentos_de_otra(
    django_user_model,
):
    primera_rendicion = _crear_rendicion()
    segunda_rendicion = _crear_rendicion()
    primer_documento = _crear_documento(primera_rendicion, nombre="Primero.pdf")
    segundo_documento = _crear_documento(segunda_rendicion, nombre="Segundo.pdf")
    usuario = django_user_model.objects.create_user(username="revisor-aislamiento")
    _otorgar_permiso(usuario, "manage_territorial_stage")

    confirmado = RendicionCuentaMensualService.registrar_visualizacion_documento(
        documento=primer_documento,
        actor=usuario,
    )

    assert confirmado is True
    primer_documento.refresh_from_db()
    segundo_documento.refresh_from_db()
    assert primer_documento.visualizacion_usuario == usuario
    assert segundo_documento.visualizacion_etapa is None
    assert segundo_documento.visualizacion_usuario is None
    assert segundo_documento.visualizacion_fecha is None
