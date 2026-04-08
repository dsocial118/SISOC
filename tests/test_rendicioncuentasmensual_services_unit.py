"""Tests for test rendicioncuentasmensual services unit."""

from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from rendicioncuentasmensual.models import DocumentacionAdjunta, RendicionCuentaMensual
from rendicioncuentasmensual.services import RendicionCuentaMensualService


def test_crear_rendicion_cuenta_mensual_success(mocker):
    comedor = SimpleNamespace(pk=10)
    payload = {
        "mes": 1,
        "anio": 2026,
        "documento_adjunto": "doc.pdf",
        "observaciones": "obs",
        "archivos_adjuntos": ["a"],
    }
    created = object()
    mock_create = mocker.patch(
        "rendicioncuentasmensual.services.RendicionCuentaMensual.objects.create",
        return_value=created,
    )
    mock_set_archivos = mocker.patch.object(
        RendicionCuentaMensualService, "_asignar_archivos_adjuntos"
    )

    result = RendicionCuentaMensualService.crear_rendicion_cuenta_mensual(
        comedor, payload
    )

    assert result is created
    mock_create.assert_called_once_with(
        comedor=comedor,
        mes=1,
        anio=2026,
        convenio=None,
        numero_rendicion=None,
        periodo_inicio=None,
        periodo_fin=None,
        estado="elaboracion",
        documento_adjunto="doc.pdf",
        observaciones="obs",
    )
    mock_set_archivos.assert_called_once_with(created, ["a"])


def test_crear_rendicion_cuenta_mensual_logs_and_raises(mocker):
    comedor = SimpleNamespace(pk=99)
    mocker.patch(
        "rendicioncuentasmensual.services.RendicionCuentaMensual.objects.create",
        side_effect=RuntimeError("db"),
    )
    mock_exc = mocker.patch("rendicioncuentasmensual.services.logger.exception")

    with pytest.raises(RuntimeError):
        RendicionCuentaMensualService.crear_rendicion_cuenta_mensual(comedor, {})

    mock_exc.assert_called_once()


def test_actualizar_rendicion_cuenta_mensual_success():
    rendicion = SimpleNamespace(
        mes=None,
        anio=None,
        documento_adjunto=None,
        observaciones=None,
        archivos_adjuntos=None,
        save=lambda: None,
    )
    payload = {
        "mes": 2,
        "anio": 2025,
        "documento_adjunto": "b.pdf",
        "observaciones": "ok",
        "archivos_adjuntos": ["x"],
    }
    result = RendicionCuentaMensualService.actualizar_rendicion_cuenta_mensual(
        rendicion, payload
    )

    assert result is rendicion
    assert rendicion.mes == 2
    assert rendicion.anio == 2025
    assert rendicion.documento_adjunto == "b.pdf"
    assert rendicion.observaciones == "ok"
    assert rendicion.archivos_adjuntos == ["x"]


def test_actualizar_rendicion_cuenta_mensual_logs_and_raises(mocker):
    payload = {"mes": 2}
    rendicion = SimpleNamespace(
        pk=5, save=mocker.Mock(side_effect=RuntimeError("boom"))
    )
    mock_exc = mocker.patch("rendicioncuentasmensual.services.logger.exception")

    with pytest.raises(RuntimeError):
        RendicionCuentaMensualService.actualizar_rendicion_cuenta_mensual(
            rendicion, payload
        )

    mock_exc.assert_called_once()


def test_eliminar_rendicion_cuenta_mensual_success():
    deleted = {"ok": False}

    def _delete():
        deleted["ok"] = True

    rendicion = SimpleNamespace(delete=_delete)

    RendicionCuentaMensualService.eliminar_rendicion_cuenta_mensual(rendicion)

    assert deleted["ok"] is True


def test_eliminar_rendicion_cuenta_mensual_logs_and_raises(mocker):
    rendicion = SimpleNamespace(pk=3, delete=mocker.Mock(side_effect=RuntimeError("x")))
    mock_exc = mocker.patch("rendicioncuentasmensual.services.logger.exception")

    with pytest.raises(RuntimeError):
        RendicionCuentaMensualService.eliminar_rendicion_cuenta_mensual(rendicion)

    mock_exc.assert_called_once()


@pytest.mark.django_db
def test_obtener_documentacion_para_detalle_anida_subsanaciones_en_historial(
    settings, tmp_path
):
    settings.MEDIA_ROOT = str(tmp_path)
    rendicion = RendicionCuentaMensual.objects.create(mes=4, anio=2026)
    observado = DocumentacionAdjunta.objects.create(
        nombre="comprobante-observado.pdf",
        categoria=DocumentacionAdjunta.CATEGORIA_COMPROBANTES,
        estado=DocumentacionAdjunta.ESTADO_SUBSANAR,
        rendicion_cuenta_mensual=rendicion,
        archivo=SimpleUploadedFile(
            "comprobante-observado.pdf",
            b"%PDF-1.4 observado",
            content_type="application/pdf",
        ),
    )
    subsanacion_vieja = DocumentacionAdjunta.objects.create(
        nombre="comprobante-subsanado-1.pdf",
        categoria=DocumentacionAdjunta.CATEGORIA_COMPROBANTES,
        estado=DocumentacionAdjunta.ESTADO_PRESENTADO,
        rendicion_cuenta_mensual=rendicion,
        documento_subsanado=observado,
        archivo=SimpleUploadedFile(
            "comprobante-subsanado-1.pdf",
            b"%PDF-1.4 v1",
            content_type="application/pdf",
        ),
    )
    subsanacion_nueva = DocumentacionAdjunta.objects.create(
        nombre="comprobante-subsanado-2.pdf",
        categoria=DocumentacionAdjunta.CATEGORIA_COMPROBANTES,
        estado=DocumentacionAdjunta.ESTADO_PRESENTADO,
        rendicion_cuenta_mensual=rendicion,
        documento_subsanado=observado,
        archivo=SimpleUploadedFile(
            "comprobante-subsanado-2.pdf",
            b"%PDF-1.4 v2",
            content_type="application/pdf",
        ),
    )

    categorias = RendicionCuentaMensualService.obtener_documentacion_para_detalle(
        rendicion
    )

    comprobantes = next(
        item
        for item in categorias
        if item["codigo"] == DocumentacionAdjunta.CATEGORIA_COMPROBANTES
    )
    assert len(comprobantes["archivos"]) == 1
    archivo = comprobantes["archivos"][0]
    assert archivo.id == subsanacion_nueva.id
    assert [item.id for item in archivo.subsanaciones_historial] == [
        subsanacion_vieja.id,
        observado.id,
    ]
    assert archivo.subsanaciones_historial[0].get_estado_visual() == "subsanado"
    assert (
        archivo.subsanaciones_historial[0].get_estado_visual_display()
        == "Subsanado"
    )


@pytest.mark.django_db
def test_obtener_documentacion_para_detalle_promueve_ultima_observacion_en_historial(
    settings, tmp_path
):
    settings.MEDIA_ROOT = str(tmp_path)
    rendicion = RendicionCuentaMensual.objects.create(mes=4, anio=2026)
    original = DocumentacionAdjunta.objects.create(
        nombre="comprobante-original.pdf",
        categoria=DocumentacionAdjunta.CATEGORIA_COMPROBANTES,
        estado=DocumentacionAdjunta.ESTADO_SUBSANAR,
        observaciones="Primera observación",
        rendicion_cuenta_mensual=rendicion,
        archivo=SimpleUploadedFile(
            "comprobante-original.pdf",
            b"%PDF-1.4 original",
            content_type="application/pdf",
        ),
    )
    observado_nuevo = DocumentacionAdjunta.objects.create(
        nombre="comprobante-reobservado.pdf",
        categoria=DocumentacionAdjunta.CATEGORIA_COMPROBANTES,
        estado=DocumentacionAdjunta.ESTADO_SUBSANAR,
        observaciones="Segunda observación",
        rendicion_cuenta_mensual=rendicion,
        documento_subsanado=original,
        archivo=SimpleUploadedFile(
            "comprobante-reobservado.pdf",
            b"%PDF-1.4 reobservado",
            content_type="application/pdf",
        ),
    )

    categorias = RendicionCuentaMensualService.obtener_documentacion_para_detalle(
        rendicion
    )

    comprobantes = next(
        item
        for item in categorias
        if item["codigo"] == DocumentacionAdjunta.CATEGORIA_COMPROBANTES
    )
    assert len(comprobantes["archivos"]) == 1
    archivo = comprobantes["archivos"][0]
    assert archivo.id == observado_nuevo.id
    assert archivo.observaciones == "Segunda observación"
    assert [item.id for item in archivo.subsanaciones_historial] == [original.id]


@pytest.mark.django_db
def test_obtener_documentacion_para_detalle_promueve_ultima_subsanacion_presentada(
    settings, tmp_path
):
    settings.MEDIA_ROOT = str(tmp_path)
    rendicion = RendicionCuentaMensual.objects.create(mes=4, anio=2026)
    observado = DocumentacionAdjunta.objects.create(
        nombre="comprobante-observado.pdf",
        categoria=DocumentacionAdjunta.CATEGORIA_COMPROBANTES,
        estado=DocumentacionAdjunta.ESTADO_SUBSANAR,
        observaciones="Archivo observado",
        rendicion_cuenta_mensual=rendicion,
        archivo=SimpleUploadedFile(
            "comprobante-observado.pdf",
            b"%PDF-1.4 observado",
            content_type="application/pdf",
        ),
    )
    subsanacion_presentada = DocumentacionAdjunta.objects.create(
        nombre="comprobante-subsanado.pdf",
        categoria=DocumentacionAdjunta.CATEGORIA_COMPROBANTES,
        estado=DocumentacionAdjunta.ESTADO_PRESENTADO,
        rendicion_cuenta_mensual=rendicion,
        documento_subsanado=observado,
        archivo=SimpleUploadedFile(
            "comprobante-subsanado.pdf",
            b"%PDF-1.4 subsanado",
            content_type="application/pdf",
        ),
    )

    categorias = RendicionCuentaMensualService.obtener_documentacion_para_detalle(
        rendicion
    )

    comprobantes = next(
        item
        for item in categorias
        if item["codigo"] == DocumentacionAdjunta.CATEGORIA_COMPROBANTES
    )
    assert len(comprobantes["archivos"]) == 1
    archivo = comprobantes["archivos"][0]
    assert archivo.id == subsanacion_presentada.id
    assert archivo.estado == DocumentacionAdjunta.ESTADO_PRESENTADO
    assert archivo.get_estado_visual() == DocumentacionAdjunta.ESTADO_PRESENTADO
    assert archivo.get_estado_visual_display() == "Presentado"
    assert [item.id for item in archivo.subsanaciones_historial] == [observado.id]


@pytest.mark.django_db
def test_obtener_documentacion_para_detalle_mantiene_vigente_reemplazo_categoria_unica(
    settings, tmp_path
):
    settings.MEDIA_ROOT = str(tmp_path)
    rendicion = RendicionCuentaMensual.objects.create(mes=4, anio=2026)
    observado = DocumentacionAdjunta.objects.create(
        nombre="formulario-iii-v1.pdf",
        categoria=DocumentacionAdjunta.CATEGORIA_FORMULARIO_III,
        estado=DocumentacionAdjunta.ESTADO_SUBSANAR,
        rendicion_cuenta_mensual=rendicion,
        archivo=SimpleUploadedFile(
            "formulario-iii-v1.pdf",
            b"%PDF-1.4 observado",
            content_type="application/pdf",
        ),
    )
    observado.delete()
    reemplazo = DocumentacionAdjunta.objects.create(
        nombre="formulario-iii-v2.pdf",
        categoria=DocumentacionAdjunta.CATEGORIA_FORMULARIO_III,
        estado=DocumentacionAdjunta.ESTADO_VALIDADO,
        rendicion_cuenta_mensual=rendicion,
        documento_subsanado=observado,
        archivo=SimpleUploadedFile(
            "formulario-iii-v2.pdf",
            b"%PDF-1.4 reemplazo",
            content_type="application/pdf",
        ),
    )

    categorias = RendicionCuentaMensualService.obtener_documentacion_para_detalle(
        rendicion
    )

    formularios = next(
        item
        for item in categorias
        if item["codigo"] == DocumentacionAdjunta.CATEGORIA_FORMULARIO_III
    )
    assert [item.id for item in formularios["archivos"]] == [reemplazo.id]
    assert getattr(formularios["archivos"][0], "subsanaciones_historial", []) == []


@pytest.mark.django_db
def test_obtener_documentos_para_descarga_pdf_respeta_orden_visible(
    settings, tmp_path
):
    settings.MEDIA_ROOT = str(tmp_path)
    rendicion = RendicionCuentaMensual.objects.create(
        mes=4,
        anio=2026,
        estado=RendicionCuentaMensual.ESTADO_FINALIZADA,
    )
    formulario = DocumentacionAdjunta.objects.create(
        nombre="formulario-ii.pdf",
        categoria=DocumentacionAdjunta.CATEGORIA_FORMULARIO_II,
        estado=DocumentacionAdjunta.ESTADO_VALIDADO,
        rendicion_cuenta_mensual=rendicion,
        archivo=SimpleUploadedFile(
            "formulario-ii.pdf",
            b"%PDF-1.4 formulario",
            content_type="application/pdf",
        ),
    )
    comprobante = DocumentacionAdjunta.objects.create(
        nombre="comprobante-observado.pdf",
        categoria=DocumentacionAdjunta.CATEGORIA_COMPROBANTES,
        estado=DocumentacionAdjunta.ESTADO_VALIDADO,
        rendicion_cuenta_mensual=rendicion,
        archivo=SimpleUploadedFile(
            "comprobante-observado.pdf",
            b"%PDF-1.4 comprobante",
            content_type="application/pdf",
        ),
    )
    subsanacion = DocumentacionAdjunta.objects.create(
        nombre="comprobante-subsanado.pdf",
        categoria=DocumentacionAdjunta.CATEGORIA_COMPROBANTES,
        estado=DocumentacionAdjunta.ESTADO_VALIDADO,
        rendicion_cuenta_mensual=rendicion,
        documento_subsanado=comprobante,
        archivo=SimpleUploadedFile(
            "comprobante-subsanado.pdf",
            b"%PDF-1.4 subsanado",
            content_type="application/pdf",
        ),
    )

    documentos = RendicionCuentaMensualService.obtener_documentos_para_descarga_pdf(
        rendicion
    )

    assert [item.id for item in documentos] == [formulario.id, subsanacion.id, comprobante.id]


def test_obtener_rendiciones_cuentas_mensuales_success(mocker):
    comedor = object()
    queryset = object()
    project_qs_mock = mocker.patch.object(
        RendicionCuentaMensualService,
        "_get_project_queryset",
        return_value=queryset,
    )

    result = RendicionCuentaMensualService.obtener_rendiciones_cuentas_mensuales(
        comedor
    )

    assert result is queryset
    project_qs_mock.assert_called_once_with(comedor)


def test_get_archivos_adjuntos_data_acepta_key_legacy_y_nueva():
    assert RendicionCuentaMensualService._get_archivos_adjuntos_data(
        {"archivos_adjuntos": ["nuevo"], "arvhios_adjuntos": ["legacy"]}
    ) == ["nuevo"]
    assert RendicionCuentaMensualService._get_archivos_adjuntos_data(
        {"arvhios_adjuntos": ["legacy"]}
    ) == ["legacy"]


def test_asignar_archivos_adjuntos_usa_manager_set_si_existe(mocker):
    manager = mocker.Mock()
    rendicion = SimpleNamespace(archivos_adjuntos=manager)

    RendicionCuentaMensualService._asignar_archivos_adjuntos(rendicion, ["a"])

    manager.set.assert_called_once_with(["a"])


def test_obtener_rendiciones_cuentas_mensuales_logs_and_raises(mocker):
    comedor = SimpleNamespace(pk=8)
    mocker.patch(
        "rendicioncuentasmensual.services.RendicionCuentaMensual.objects.filter",
        side_effect=RuntimeError("db"),
    )
    mock_exc = mocker.patch("rendicioncuentasmensual.services.logger.exception")

    with pytest.raises(RuntimeError):
        RendicionCuentaMensualService.obtener_rendiciones_cuentas_mensuales(comedor)

    mock_exc.assert_called_once()


def test_obtener_rendicion_cuenta_mensual_success(mocker):
    expected = object()
    mock_get = mocker.patch(
        "rendicioncuentasmensual.services.get_object_or_404", return_value=expected
    )

    result = RendicionCuentaMensualService.obtener_rendicion_cuenta_mensual(12)

    assert result is expected
    mock_get.assert_called_once()


def test_obtener_rendicion_cuenta_mensual_logs_and_raises(mocker):
    mocker.patch(
        "rendicioncuentasmensual.services.get_object_or_404",
        side_effect=RuntimeError("404"),
    )
    mock_exc = mocker.patch("rendicioncuentasmensual.services.logger.exception")

    with pytest.raises(RuntimeError):
        RendicionCuentaMensualService.obtener_rendicion_cuenta_mensual(77)

    mock_exc.assert_called_once()


def test_cantidad_rendiciones_cuentas_mensuales_success(mocker):
    comedor = object()
    project_qs = mocker.Mock()
    project_qs.count.return_value = 5
    project_qs_mock = mocker.patch.object(
        RendicionCuentaMensualService,
        "_get_project_queryset",
        return_value=project_qs,
    )

    assert (
        RendicionCuentaMensualService.cantidad_rendiciones_cuentas_mensuales(comedor)
        == 5
    )
    project_qs_mock.assert_called_once_with(comedor)
    project_qs.count.assert_called_once_with()


def test_cantidad_rendiciones_cuentas_mensuales_logs_and_raises(mocker):
    comedor = SimpleNamespace(pk=2)
    mocker.patch(
        "rendicioncuentasmensual.services.RendicionCuentaMensual.objects.filter",
        side_effect=RuntimeError("err"),
    )
    mock_exc = mocker.patch("rendicioncuentasmensual.services.logger.exception")

    with pytest.raises(RuntimeError):
        RendicionCuentaMensualService.cantidad_rendiciones_cuentas_mensuales(comedor)

    mock_exc.assert_called_once()


def test_obtener_scope_proyecto_con_codigo_y_organizacion(mocker):
    organizacion = SimpleNamespace(nombre="Organizacion A")
    comedor = SimpleNamespace(
        organizacion=organizacion,
        organizacion_id=5,
        codigo_de_proyecto="PROY-01",
        nombre="Comedor Base",
    )
    rendicion = SimpleNamespace(comedor=comedor)
    expected = [
        SimpleNamespace(nombre="Comedor 1"),
        SimpleNamespace(nombre="Comedor 2"),
    ]
    filter_mock = mocker.patch(
        "rendicioncuentasmensual.services.Comedor.objects.filter",
        return_value=SimpleNamespace(order_by=lambda *_args: expected),
    )

    result = RendicionCuentaMensualService.obtener_scope_proyecto(rendicion)

    assert result["organizacion"] is organizacion
    assert result["proyecto_codigo"] == "PROY-01"
    assert result["comedores_relacionados"] == expected
    filter_mock.assert_called_once_with(
        codigo_de_proyecto="PROY-01",
        deleted_at__isnull=True,
        organizacion_id=5,
    )


def test_obtener_scope_proyecto_sin_codigo_retorna_comedor_actual():
    comedor = SimpleNamespace(
        organizacion=None,
        organizacion_id=None,
        codigo_de_proyecto="",
        nombre="Comedor Unico",
    )
    rendicion = SimpleNamespace(comedor=comedor)

    result = RendicionCuentaMensualService.obtener_scope_proyecto(rendicion)

    assert result["organizacion"] is None
    assert result["proyecto_codigo"] == ""
    assert result["comedores_relacionados"] == [comedor]


@pytest.mark.django_db
def test_actualizar_estado_documento_revision_valida_documento_y_finaliza_rendicion(
    mocker,
):
    actor = SimpleNamespace(id=10, is_authenticated=True)
    rendicion = SimpleNamespace(
        estado=RendicionCuentaMensual.ESTADO_REVISION,
        usuario_ultima_modificacion=None,
        save=mocker.Mock(),
    )
    documento = SimpleNamespace(
        estado=DocumentacionAdjunta.ESTADO_PRESENTADO,
        observaciones=None,
        rendicion_cuenta_mensual=rendicion,
        save=mocker.Mock(),
    )
    sync_mock = mocker.patch.object(
        RendicionCuentaMensualService,
        "_sincronizar_estado_rendicion_por_documentos",
    )
    notify_mock = mocker.patch.object(
        RendicionCuentaMensualService,
        "_crear_notificacion_mobile_revision_documento",
    )

    resultado = RendicionCuentaMensualService.actualizar_estado_documento_revision(
        documento=documento,
        estado=DocumentacionAdjunta.ESTADO_VALIDADO,
        observaciones="No aplica",
        actor=actor,
    )

    assert resultado is documento
    assert documento.estado == DocumentacionAdjunta.ESTADO_VALIDADO
    assert documento.observaciones is None
    assert rendicion.usuario_ultima_modificacion is actor
    documento.save.assert_called_once_with(
        update_fields=["estado", "observaciones", "ultima_modificacion"]
    )
    rendicion.save.assert_called_once_with(
        update_fields=["usuario_ultima_modificacion", "ultima_modificacion"]
    )
    sync_mock.assert_called_once_with(rendicion)
    notify_mock.assert_called_once_with(documento=documento, actor=actor)


@pytest.mark.django_db
def test_crear_notificacion_mobile_revision_documento_genera_comunicado_targeteado(
    mocker,
):
    comedor = SimpleNamespace(id=5, codigo_de_proyecto="PROY-14")
    rendicion = SimpleNamespace(
        id=14,
        numero_rendicion="RCM-14",
        convenio="CONV-14",
        estado=RendicionCuentaMensual.ESTADO_SUBSANAR,
        comedor=comedor,
    )
    documento = SimpleNamespace(
        nombre="comprobante.pdf",
        observaciones="Falta ticket legible",
        rendicion_cuenta_mensual=rendicion,
        get_estado_display=lambda: "A subsanar",
    )
    comunicado = SimpleNamespace(comedores=SimpleNamespace(add=mocker.Mock()))
    create_mock = mocker.patch(
        "rendicioncuentasmensual.services.Comunicado.objects.create",
        return_value=comunicado,
    )
    destinos_mock = mocker.patch.object(
        RendicionCuentaMensualService,
        "_obtener_comedores_destino_notificacion",
        return_value=[comedor],
    )
    actor = SimpleNamespace(id=2)

    resultado = (
        RendicionCuentaMensualService._crear_notificacion_mobile_revision_documento(
            documento=documento,
            actor=actor,
        )
    )

    assert resultado is comunicado
    create_mock.assert_called_once()
    kwargs = create_mock.call_args.kwargs
    assert "Proyecto PROY-14 | Convenio CONV-14 |" in kwargs["titulo"]
    assert "documento a subsanar" in kwargs["titulo"]
    assert "Estado: A subsanar." in kwargs["cuerpo"]
    assert "Observaciones: Falta ticket legible." in kwargs["cuerpo"]
    assert "Presentación a subsanar" in kwargs["cuerpo"]
    assert kwargs["fecha_publicacion"] is not None
    destinos_mock.assert_called_once_with(rendicion)
    comunicado.comedores.add.assert_called_once_with(comedor)


@pytest.mark.django_db
def test_crear_notificacion_mobile_revision_documento_archiva_previas(mocker):
    comedor = SimpleNamespace(id=5, codigo_de_proyecto="PROY-14")
    rendicion = SimpleNamespace(
        id=14,
        numero_rendicion="RCM-14",
        convenio="CONV-14",
        estado=RendicionCuentaMensual.ESTADO_SUBSANAR,
        comedor=comedor,
    )
    documento = SimpleNamespace(
        nombre="comprobante.pdf",
        observaciones=None,
        rendicion_cuenta_mensual=rendicion,
        get_estado_display=lambda: "A subsanar",
    )
    mocker.patch(
        "rendicioncuentasmensual.services.Comunicado.objects.create",
        return_value=SimpleNamespace(comedores=SimpleNamespace(add=mocker.Mock())),
    )
    mocker.patch.object(
        RendicionCuentaMensualService,
        "_obtener_comedores_destino_notificacion",
        return_value=[comedor],
    )
    mocker.patch("rendicioncuentasmensual.services.notify_rendicion_revision_push")
    archive_mock = mocker.patch.object(
        RendicionCuentaMensualService,
        "_archivar_notificaciones_mobile_rendicion",
    )

    RendicionCuentaMensualService._crear_notificacion_mobile_revision_documento(
        documento=documento,
        actor=SimpleNamespace(id=2),
    )

    archive_mock.assert_called_once_with(rendicion)


@pytest.mark.django_db
def test_crear_notificacion_mobile_revision_documento_no_publica_si_finaliza(
    mocker,
):
    comedor = SimpleNamespace(id=5, codigo_de_proyecto="PROY-14")
    rendicion = SimpleNamespace(
        id=14,
        numero_rendicion="RCM-14",
        convenio="CONV-14",
        estado=RendicionCuentaMensual.ESTADO_FINALIZADA,
        comedor=comedor,
    )
    documento = SimpleNamespace(
        nombre="comprobante.pdf",
        observaciones=None,
        rendicion_cuenta_mensual=rendicion,
        get_estado_display=lambda: "Validado",
    )
    create_mock = mocker.patch(
        "rendicioncuentasmensual.services.Comunicado.objects.create"
    )
    archive_mock = mocker.patch.object(
        RendicionCuentaMensualService,
        "_archivar_notificaciones_mobile_rendicion",
    )

    resultado = (
        RendicionCuentaMensualService._crear_notificacion_mobile_revision_documento(
            documento=documento,
            actor=SimpleNamespace(id=2),
        )
    )

    assert resultado is None
    archive_mock.assert_called_once_with(rendicion)
    create_mock.assert_not_called()


@pytest.mark.django_db
def test_actualizar_estado_documento_revision_exige_observacion_para_subsanar():
    rendicion = SimpleNamespace(estado=RendicionCuentaMensual.ESTADO_REVISION)
    documento = SimpleNamespace(
        estado=DocumentacionAdjunta.ESTADO_PRESENTADO,
        rendicion_cuenta_mensual=rendicion,
    )

    with pytest.raises(ValidationError) as exc_info:
        RendicionCuentaMensualService.actualizar_estado_documento_revision(
            documento=documento,
            estado=DocumentacionAdjunta.ESTADO_SUBSANAR,
            observaciones="   ",
        )

    assert "Debe ingresar observaciones" in str(exc_info.value)


def test_sincronizar_estado_rendicion_por_documentos_mueve_a_subsanar(mocker):
    rendicion = SimpleNamespace(
        estado=RendicionCuentaMensual.ESTADO_REVISION,
        save=mocker.Mock(),
    )
    documentos = [
        SimpleNamespace(estado=DocumentacionAdjunta.ESTADO_VALIDADO),
        SimpleNamespace(estado=DocumentacionAdjunta.ESTADO_SUBSANAR),
    ]
    mocker.patch.object(
        RendicionCuentaMensualService,
        "_documentos_vigentes_queryset",
        return_value=documentos,
    )

    RendicionCuentaMensualService._sincronizar_estado_rendicion_por_documentos(
        rendicion
    )

    assert rendicion.estado == RendicionCuentaMensual.ESTADO_SUBSANAR
    rendicion.save.assert_called_once_with(
        update_fields=["estado", "ultima_modificacion"]
    )


def test_sincronizar_estado_rendicion_por_documentos_mueve_a_finalizada(mocker):
    rendicion = SimpleNamespace(
        estado=RendicionCuentaMensual.ESTADO_SUBSANAR,
        save=mocker.Mock(),
    )
    documentos = [
        SimpleNamespace(estado=DocumentacionAdjunta.ESTADO_VALIDADO),
        SimpleNamespace(estado=DocumentacionAdjunta.ESTADO_VALIDADO),
    ]
    mocker.patch.object(
        RendicionCuentaMensualService,
        "_documentos_vigentes_queryset",
        return_value=documentos,
    )

    RendicionCuentaMensualService._sincronizar_estado_rendicion_por_documentos(
        rendicion
    )

    assert rendicion.estado == RendicionCuentaMensual.ESTADO_FINALIZADA
    rendicion.save.assert_called_once_with(
        update_fields=["estado", "ultima_modificacion"]
    )


def test_sincronizar_estado_rendicion_por_documentos_archiva_notificaciones_si_sale_de_subsanar(
    mocker,
):
    rendicion = SimpleNamespace(
        estado=RendicionCuentaMensual.ESTADO_SUBSANAR,
        save=mocker.Mock(),
    )
    documentos = [
        SimpleNamespace(estado=DocumentacionAdjunta.ESTADO_VALIDADO),
    ]
    mocker.patch.object(
        RendicionCuentaMensualService,
        "_documentos_vigentes_queryset",
        return_value=documentos,
    )
    archive_mock = mocker.patch.object(
        RendicionCuentaMensualService,
        "_archivar_notificaciones_mobile_rendicion",
    )

    RendicionCuentaMensualService._sincronizar_estado_rendicion_por_documentos(
        rendicion
    )

    archive_mock.assert_called_once_with(rendicion)


@pytest.mark.django_db
def test_presentar_rendicion_mobile_rechaza_documentos_observados_vigentes(mocker):
    rendicion = SimpleNamespace(
        estado=RendicionCuentaMensual.ESTADO_SUBSANAR,
        documento_adjunto=True,
    )
    documento = SimpleNamespace(estado=DocumentacionAdjunta.ESTADO_SUBSANAR)
    mocker.patch.object(
        RendicionCuentaMensualService,
        "validar_documentacion_obligatoria",
    )
    mocker.patch.object(
        RendicionCuentaMensualService,
        "_sincronizar_flag_documento_adjunto",
    )
    mocker.patch.object(
        RendicionCuentaMensualService,
        "_documentos_vigentes_queryset",
        return_value=[documento],
    )

    with pytest.raises(ValidationError) as exc_info:
        RendicionCuentaMensualService.presentar_rendicion_mobile(rendicion)

    assert "pendiente de subsanar" in str(exc_info.value)
