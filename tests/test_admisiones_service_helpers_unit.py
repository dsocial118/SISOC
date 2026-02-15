"""Tests for test admisiones service helpers unit."""

from datetime import datetime
from types import SimpleNamespace
from io import BytesIO

from django.utils import timezone

from admisiones.services import admisiones_service as module


class _ListChain(list):
    """Minimal queryset-like list for service unit tests."""

    def select_related(self, *_args, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def first(self):
        return self[0] if self else None

    def filter(self, **_kwargs):
        return self


def test_estado_normalization_and_resumen_helpers():
    disp, val = module.AdmisionService._normalize_estado_display(" a validar abogado ")
    assert (disp, val) == ("A Validar Abogado", "A Validar Abogado")

    disp2, val2 = module.AdmisionService._estado_display_y_valor("desconocido")
    assert (disp2, val2) == ("desconocido", "desconocido")

    resumen = module.AdmisionService._resumen_documentos(
        [{"estado": "pendiente"}, {"estado": "Aceptado"}],
        [{"estado": "Rectificar"}],
    )
    assert resumen["Pendiente"] == 1
    assert resumen["Aceptado"] == 1
    assert resumen["Rectificar"] == 1

    stats = module.AdmisionService._stats_from_resumen(resumen, 5, 2)
    assert stats["obligatorios_total"] == 5
    assert stats["obligatorios_completos"] == 2


def test_archivo_nombre_and_serialization():
    archivo = SimpleNamespace(nombre_personalizado="Doc X", archivo=None)
    assert module.AdmisionService._archivo_nombre(archivo) == "Doc X"

    archivo2 = SimpleNamespace(nombre_personalizado=None, archivo=SimpleNamespace(name="/tmp/a.pdf"))
    assert module.AdmisionService._archivo_nombre(archivo2) == "a.pdf"

    doc = SimpleNamespace(id=1, nombre="DNI", obligatorio=True)
    archivo3 = SimpleNamespace(
        id=2,
        estado="pendiente",
        archivo=SimpleNamespace(url="/m.pdf"),
        numero_gde="gde",
        observaciones="obs",
    )
    ser = module.AdmisionService._serialize_documentacion(doc, archivo3)
    assert ser["documentacion_id"] == 1
    assert ser["archivo_id"] == 2
    assert ser["estado"] == "Pendiente"

    pers = module.AdmisionService.serialize_documento_personalizado(
        SimpleNamespace(
            id=9,
            estado="Aceptado",
            archivo=SimpleNamespace(url="/x"),
            numero_gde="1",
            observaciones="o",
            nombre_personalizado="Extra",
        )
    )
    assert pers["es_personalizado"] is True
    assert pers["row_id"] == "custom-9"


def test_apply_text_search_and_queryset_passthrough():
    qs = SimpleNamespace(filter=lambda *_args, **_kwargs: "filtered")
    assert module.AdmisionService._apply_admisiones_text_search(qs, "") is qs
    assert module.AdmisionService._apply_admisiones_text_search(qs, "abc") == "filtered"


def test_get_table_data_and_date_formatting(mocker):
    aware_dt = timezone.make_aware(datetime(2026, 1, 1, 10, 0))
    comedor = SimpleNamespace(
        id=3,
        nombre="Comedor",
        tipocomedor="Tipo",
        provincia="Prov",
        referente=SimpleNamespace(nombre="N", apellido="A", celular="1"),
        dupla="Dupla",
        organizacion=SimpleNamespace(nombre="Org"),
    )
    adm = SimpleNamespace(
        id=1,
        pk=1,
        comedor=comedor,
        tipo="x",
        get_tipo_display=lambda: "TipoAdm",
        convenio_numero=12,
        num_expediente="EXP-1",
        estado_admision="pendiente",
        get_estado_admision_display=lambda: "Pendiente",
        modificado=aware_dt,
        estado_legales="A Rectificar",
    )

    mocker.patch("admisiones.services.admisiones_service.reverse", side_effect=lambda name, args=None: f"/{name}/{args[0] if args else ''}")
    mocker.patch("django.utils.safestring.mark_safe", side_effect=lambda x: x)

    rows = module.AdmisionService.get_admisiones_tecnicos_table_data([adm, adm], SimpleNamespace())
    assert len(rows) == 1
    assert rows[0]["cells"][0]["content"] == "3"


def test_get_admisiones_tecnicos_queryset_superuser_and_query_modes(mocker):
    class Qs:
        def __init__(self):
            self.calls = []

        def exclude(self, *a, **k):
            self.calls.append("exclude")
            return self

        def values_list(self, *a, **k):
            return self

        def distinct(self):
            return [1, 2]

        def filter(self, *a, **k):
            self.calls.append("filter")
            return self

        def select_related(self, *a, **k):
            return self

        def order_by(self, *a, **k):
            return "ordered"

    qs = Qs()
    mocker.patch("admisiones.services.admisiones_service.Admision.objects.all", return_value=qs)
    mocker.patch("admisiones.services.admisiones_service.ADMISION_ADVANCED_FILTER.filter_queryset", side_effect=lambda q, _: q)
    mocker.patch.object(module.AdmisionService, "_apply_admisiones_text_search", side_effect=lambda q, _: q)
    mocker.patch("admisiones.services.admisiones_service.Admision.objects.filter", return_value=qs)

    user = SimpleNamespace(is_superuser=True)
    req = SimpleNamespace(GET={"busqueda": "x"})
    assert module.AdmisionService.get_admisiones_tecnicos_queryset(user, req) == "ordered"

    req_map = {"busqueda": "x"}
    assert module.AdmisionService.get_admisiones_tecnicos_queryset(user, req_map) == "ordered"

    assert module.AdmisionService.get_admisiones_tecnicos_queryset(user, "texto") == "ordered"


def test_post_update_router_and_update_convenio(mocker):
    """POST update router should dispatch each action and update convenio branch."""
    adm = SimpleNamespace(pk=1, estado_admision="convenio_seleccionado", save=mocker.Mock(), refresh_from_db=mocker.Mock())
    req = SimpleNamespace(POST={"mandarLegales": "1"}, user=SimpleNamespace())

    mocker.patch.object(module.AdmisionService, "marcar_como_enviado_a_legales", return_value=True)
    upd = mocker.patch.object(module.AdmisionService, "actualizar_estado_admision")
    ok, _msg = module.AdmisionService.procesar_post_update(req, adm)
    assert ok is True
    assert upd.called

    req_if = SimpleNamespace(POST={"btnIFInformeTecnico": "1"}, user=SimpleNamespace())
    mocker.patch.object(module.AdmisionService, "guardar_if_informe_tecnico", return_value=(True, "ok"))
    ok_if, _ = module.AdmisionService.procesar_post_update(req_if, adm)
    assert ok_if is True

    # update_convenio
    conv = SimpleNamespace(pk=8)
    mocker.patch("admisiones.services.admisiones_service.TipoConvenio.objects.get", return_value=conv)
    mocker.patch("admisiones.services.admisiones_service.ArchivoAdmision.objects.filter", return_value=SimpleNamespace(delete=mocker.Mock()))
    assert module.AdmisionService.update_convenio(adm, 8) is True


def test_handle_upload_personalizado_and_delete_file(mocker):
    """Upload and delete helpers should manage file records and transitions."""
    admision = SimpleNamespace(pk=1, estado_admision="convenio_seleccionado", save=mocker.Mock())
    doc = SimpleNamespace(pk=2, convenios=SimpleNamespace(exists=lambda: False), delete=mocker.Mock())
    archivo_obj = SimpleNamespace(documentacion=doc, archivo="f.txt", delete=mocker.Mock(), admision=admision, pk=4)

    mocker.patch("admisiones.services.admisiones_service.get_object_or_404", side_effect=[admision, doc])
    upsert = mocker.patch(
        "admisiones.services.admisiones_service.ArchivoAdmision.objects.update_or_create",
        return_value=(SimpleNamespace(creado_por=None, save=mocker.Mock(), admision=admision), True),
    )
    mocker.patch.object(module.AdmisionService, "actualizar_estado_admision")
    got, created = module.AdmisionService.handle_file_upload(1, 2, archivo="x", usuario=SimpleNamespace(is_authenticated=True))
    assert created is True
    assert got is not None
    assert upsert.called

    # crear documento personalizado
    mocker.patch("admisiones.services.admisiones_service.get_object_or_404", return_value=SimpleNamespace(comedor="c"))
    mocker.patch.object(module.AdmisionService, "_verificar_permiso_dupla", return_value=True)
    mocker.patch("admisiones.services.admisiones_service.transaction.atomic", return_value=__import__("contextlib").nullcontext())
    create = mocker.patch("admisiones.services.admisiones_service.ArchivoAdmision.objects.create", return_value=SimpleNamespace(pk=9))
    docx, err = module.AdmisionService.crear_documento_personalizado(1, "Nombre", archivo="bin", usuario=SimpleNamespace(is_superuser=False, is_authenticated=True))
    assert err is None and docx.pk == 9
    assert create.called

    # delete file helper
    mocker.patch("admisiones.services.admisiones_service.os.path.exists", return_value=False)
    mocker.patch("admisiones.services.admisiones_service.ArchivoAdmision.objects.filter", return_value=SimpleNamespace(exists=lambda: False))
    module.AdmisionService.delete_admision_file(archivo_obj)
    assert archivo_obj.delete.called


def test_actualizar_estado_ajax_and_update_estado_archivo(mocker):
    """AJAX state update should validate payload, permissions and observation rules."""
    req_bad = SimpleNamespace(POST={}, user=SimpleNamespace(is_superuser=True))
    out_bad = module.AdmisionService.actualizar_estado_ajax(req_bad)
    assert out_bad["success"] is False

    adm = SimpleNamespace(comedor=SimpleNamespace())
    archivo = SimpleNamespace(observaciones="", admision=adm, save=mocker.Mock())

    req = SimpleNamespace(
        POST={"estado": "Rectificar", "documento_id": "2", "admision_id": "1", "observacion": "obs"},
        user=SimpleNamespace(is_superuser=False),
    )
    mocker.patch("admisiones.services.admisiones_service.get_object_or_404", side_effect=[adm, archivo])
    mocker.patch.object(module.AdmisionService, "_verificar_permiso_dupla", return_value=True)
    mocker.patch.object(module.AdmisionService, "get_dupla_grupo_por_usuario", return_value="Abogado Dupla")
    upd_mock = mocker.patch.object(module.AdmisionService, "update_estado_archivo", return_value=True)
    out = module.AdmisionService.actualizar_estado_ajax(req)
    assert out["success"] is True
    assert upd_mock.called


def test_update_estado_archivo_none_returns_false():
    """update_estado_archivo should fail fast for empty file object."""
    assert module.AdmisionService.update_estado_archivo(None, "x") is False


def test_marcar_envios_y_rectificacion_documentacion():
    """Cubre cambios de flags para legales, acompañamiento y rectificación."""
    adm = SimpleNamespace(
        pk=1,
        enviado_legales=False,
        enviado_acompaniamiento=False,
        estado_legales="X",
        estado_id=1,
        observaciones="obs",
        save=lambda: None,
    )
    assert module.AdmisionService.marcar_como_enviado_a_legales(adm) is True
    assert adm.enviado_legales is True
    assert module.AdmisionService.marcar_como_enviado_a_acompaniamiento(adm) is True
    assert adm.enviado_acompaniamiento is True
    assert module.AdmisionService.marcar_como_documentacion_rectificada(adm) is True
    assert adm.estado_legales == "Rectificado"
    assert adm.observaciones is None


def test_guardar_if_informe_tecnico_paths(mocker):
    """Valida ramas de formulario IF técnico válido, inválido y excepción."""
    req = SimpleNamespace(POST={}, FILES={})
    adm = SimpleNamespace(pk=2)

    valid = mocker.Mock(is_valid=mocker.Mock(return_value=True), save=mocker.Mock())
    mocker.patch("admisiones.services.admisiones_service.IFInformeTecnicoForm", return_value=valid)
    ok, _ = module.AdmisionService.guardar_if_informe_tecnico(req, adm)
    assert ok is True

    invalid = mocker.Mock(is_valid=mocker.Mock(return_value=False))
    mocker.patch("admisiones.services.admisiones_service.IFInformeTecnicoForm", return_value=invalid)
    ok2, _ = module.AdmisionService.guardar_if_informe_tecnico(req, adm)
    assert ok2 is False

    mocker.patch("admisiones.services.admisiones_service.IFInformeTecnicoForm", side_effect=RuntimeError("boom"))
    ok3, _ = module.AdmisionService.guardar_if_informe_tecnico(req, adm)
    assert ok3 is False


def test_actualizar_numero_gde_ajax_validations(mocker):
    """Cubre validaciones y éxito del endpoint AJAX de número GDE."""
    req_missing = SimpleNamespace(POST={}, user=SimpleNamespace(is_superuser=True))
    assert module.AdmisionService.actualizar_numero_gde_ajax(req_missing)["success"] is False

    archivo = SimpleNamespace(
        estado="Aceptado",
        numero_gde="OLD",
        admision=SimpleNamespace(comedor=SimpleNamespace()),
        save=mocker.Mock(),
    )
    req = SimpleNamespace(
        POST={"documento_id": "1", "numero_gde": "GDE-1"},
        user=SimpleNamespace(is_superuser=False),
    )
    mocker.patch("admisiones.services.admisiones_service.get_object_or_404", return_value=archivo)
    mocker.patch.object(module.AdmisionService, "_verificar_permiso_dupla", return_value=True)
    out = module.AdmisionService.actualizar_numero_gde_ajax(req)
    assert out["success"] is True
    assert out["numero_gde"] == "GDE-1"

    archivo.estado = "Pendiente"
    out2 = module.AdmisionService.actualizar_numero_gde_ajax(req)
    assert out2["success"] is False


def test_actualizar_convenio_numero_ajax_branches(mocker):
    """Valida permisos, parseo numérico y persistencia de convenio_numero."""
    req_no_id = SimpleNamespace(POST={}, user=SimpleNamespace(is_superuser=True))
    assert module.AdmisionService.actualizar_convenio_numero_ajax(req_no_id)["success"] is False

    adm = SimpleNamespace(convenio_numero=2, comedor=SimpleNamespace(), save=mocker.Mock())
    req = SimpleNamespace(POST={"admision_id": "1", "convenio_numero": "5"}, user=SimpleNamespace(is_superuser=True))
    mocker.patch("admisiones.services.admisiones_service.get_object_or_404", return_value=adm)
    out = module.AdmisionService.actualizar_convenio_numero_ajax(req)
    assert out["success"] is True
    assert out["convenio_numero"] == 5

    req_bad = SimpleNamespace(POST={"admision_id": "1", "convenio_numero": "abc"}, user=SimpleNamespace(is_superuser=True))
    assert module.AdmisionService.actualizar_convenio_numero_ajax(req_bad)["success"] is False


def test_permiso_helpers_y_botones_disponibles():
    """Verifica permisos técnicos/dupla y cálculo de botones en estados clave."""
    user = SimpleNamespace(
        id=9,
        groups=SimpleNamespace(filter=lambda **k: SimpleNamespace(exists=lambda: k.get("name") == "Tecnico Comedor")),
    )
    comedor = SimpleNamespace(dupla=SimpleNamespace(tecnico=SimpleNamespace(filter=lambda **k: SimpleNamespace(exists=lambda: True)), abogado=None, estado="Activo"))
    assert module.AdmisionService._verificar_permiso_tecnico_dupla(user, comedor) is True
    assert module.AdmisionService._verificar_permiso_dupla(SimpleNamespace(id=3), comedor) is True

    adm = SimpleNamespace(
        numero_disposicion=None,
        enviado_acompaniamiento=False,
        estado_legales="A Rectificar",
        estado_admision="if_informe_tecnico_cargado",
        num_expediente="EXP",
        numero_if_tecnico=None,
        enviado_legales=False,
    )
    informe = SimpleNamespace(estado="Validado", estado_formulario="borrador")
    botones = module.AdmisionService._get_botones_disponibles(adm, informe, True, user=SimpleNamespace(groups=user.groups))
    assert "rectificar_documentacion" in botones


def test_transiciones_estado_y_helpers_obligatorios(mocker):
    """Cubre transiciones de estado y chequeos de documentos obligatorios."""
    adm = SimpleNamespace(pk=4, estado_admision="convenio_seleccionado", estado_id=1, tipo_convenio=object(), save=mocker.Mock())
    assert module.AdmisionService.actualizar_estado_admision(adm, "cargar_documento") is True
    assert adm.estado_admision == "documentacion_en_proceso"
    assert module.AdmisionService.actualizar_estado_admision(adm, "accion_inexistente") is False

    docs = [SimpleNamespace(pk=1), SimpleNamespace(pk=2)]
    mocker.patch("admisiones.services.admisiones_service.Documentacion.objects.filter", return_value=docs)
    mocker.patch(
        "admisiones.services.admisiones_service.ArchivoAdmision.objects.filter",
        side_effect=[SimpleNamespace(first=lambda: SimpleNamespace()), SimpleNamespace(first=lambda: None)],
    )
    assert module.AdmisionService._todos_obligatorios_aceptados(adm) is False

    mocker.patch("admisiones.services.admisiones_service.Documentacion.objects.filter", return_value=[SimpleNamespace(pk=1)])
    mocker.patch("admisiones.services.admisiones_service.ArchivoAdmision.objects.filter", return_value=SimpleNamespace(first=lambda: SimpleNamespace(archivo="x")))
    assert module.AdmisionService._todos_obligatorios_tienen_archivos(adm) is True


def test_actualizar_estados_por_cambio_documento(mocker):
    """Actualiza estado documental según rectificación y completitud obligatoria."""
    adm = SimpleNamespace(pk=5, estado_admision="documentacion_finalizada", estado_id=1, save=mocker.Mock())
    mocker.patch.object(module.AdmisionService, "_todos_obligatorios_aceptados", return_value=False)
    module.AdmisionService._actualizar_estados_por_cambio_documento(adm, "Rectificar")
    assert adm.estado_admision == "documentacion_en_proceso"

    adm2 = SimpleNamespace(pk=6, estado_admision="documentacion_en_proceso", estado_id=1, save=mocker.Mock())
    mocker.patch.object(module.AdmisionService, "_todos_obligatorios_tienen_archivos", return_value=True)
    mocker.patch.object(module.AdmisionService, "_todos_obligatorios_aceptados", return_value=True)
    module.AdmisionService._actualizar_estados_por_cambio_documento(adm2, "Aceptado")
    assert adm2.estado_admision == "documentacion_aprobada"


def test_get_contexts_and_comenzar_acompanamiento(mocker):
    """Valida context builders y flujo de comienzo de acompañamiento."""
    adm = SimpleNamespace(pk=7, comedor=SimpleNamespace(nombre="C"), save=mocker.Mock())
    mocker.patch("admisiones.services.admisiones_service.get_object_or_404", return_value=adm)
    mocker.patch("admisiones.services.admisiones_service.EstadoAdmision.objects.get", return_value="estado")
    importar = mocker.patch("admisiones.services.admisiones_service.AcompanamientoService.importar_datos_desde_admision")
    assert module.AdmisionService.comenzar_acompanamiento(7) is adm
    assert importar.called

    ctx = module.AdmisionService.get_admision_context(7)
    assert ctx["admision"] is adm
    assert module.AdmisionService.get_admision_instance(7) is adm


def test_generar_documento_admision_and_update_context(mocker):
    """Genera DOCX de admisión y arma contexto update con estadísticas."""
    adm = SimpleNamespace(
        pk=8,
        tipo_convenio=object(),
        comedor=SimpleNamespace(nombre="Comedor X"),
        estado_legales="Informe Complementario Solicitado",
        observaciones_informe_tecnico_complementario="obs",
    )
    mocker.patch("admisiones.services.admisiones_service.TextFormatterService.preparar_contexto_admision", return_value={})
    mocker.patch("admisiones.services.admisiones_service.DocumentTemplateService.generar_docx", return_value=BytesIO(b"doc"))
    out = module.AdmisionService.generar_documento_admision(SimpleNamespace(id=1, comedor=SimpleNamespace(nombre="Comedor X")))
    assert out is not None

    docs = [SimpleNamespace(id=1, nombre="Doc", obligatorio=True)]
    archs = _ListChain([SimpleNamespace(id=2, documentacion_id=1, documentacion=SimpleNamespace(id=1), estado="Aceptado", archivo=SimpleNamespace(url="/a"), numero_gde="1", observaciones="o")])
    informes_comp = _ListChain([SimpleNamespace(estado="rectificar", observaciones_legales="detalle")])
    mocker.patch("admisiones.services.admisiones_service.Documentacion.objects.filter", return_value=SimpleNamespace(distinct=lambda: SimpleNamespace(order_by=lambda *_: docs)))
    mocker.patch("admisiones.services.admisiones_service.ArchivoAdmision.objects.filter", return_value=archs)
    mocker.patch("admisiones.services.admisiones_service.TipoConvenio.objects.exclude", return_value=["conv"])
    mocker.patch("admisiones.services.admisiones_service.CaratularForm", return_value="f1")
    mocker.patch("admisiones.services.admisiones_service.IFInformeTecnicoForm", return_value="f2")
    mocker.patch("admisiones.services.admisiones_service.InformeTecnico.objects.filter", return_value=SimpleNamespace(order_by=lambda *_: SimpleNamespace(first=lambda: None)))
    mocker.patch("admisiones.services.admisiones_service.InformeComplementario.objects.filter", return_value=informes_comp)
    mocker.patch("admisiones.services.admisiones_service.InformeTecnicoPDF.objects.filter", return_value=SimpleNamespace(first=lambda: None))
    mocker.patch.object(module.AdmisionService, "_get_botones_disponibles", return_value=["b"])
    mocker.patch.object(module.AdmisionService, "_verificar_permiso_tecnico_dupla", return_value=True)

    ctx = module.AdmisionService.get_admision_update_context(adm, user=SimpleNamespace(is_superuser=False))
    assert ctx["obligatorios_totales"] == 1
    assert ctx["stats"]["aceptados"] == 1
