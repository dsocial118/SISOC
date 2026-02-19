"""Tests for test legales service unit."""

from contextlib import nullcontext
from io import BytesIO
from datetime import datetime
from types import SimpleNamespace

from django.utils import timezone

from admisiones.services import legales_service as module


class _Chain:
    def __init__(self, data):
        self._data = data

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __getitem__(self, item):
        return self._data[item]

    def first(self):
        return self._data[0] if self._data else None

    def order_by(self, *_args, **_kwargs):
        return self

    def filter(self, **kwargs):
        data = self._data
        if "tipo" in kwargs:
            target = kwargs["tipo"]
            data = [item for item in data if getattr(item, "tipo", None) == target]
        return _Chain(data)


def _build_formulario_fake(mocker):
    return SimpleNamespace(
        admision=None,
        tipo=None,
        creado_por=None,
        archivo=SimpleNamespace(delete=mocker.Mock(), save=mocker.Mock()),
        archivo_docx=SimpleNamespace(delete=mocker.Mock(), save=mocker.Mock()),
        save=mocker.Mock(),
    )


def test_normalizar_and_format_datetime():
    assert module.normalizar(" ÁéÍ ") == "aei"
    assert module.normalizar("") == ""

    assert module._format_datetime(None, "%d/%m/%Y") == "-"
    naive = datetime(2026, 1, 2, 3, 4)
    assert module._format_datetime(naive, "%d/%m/%Y") == "02/01/2026"

    aware = timezone.make_aware(datetime(2026, 1, 2, 3, 4))
    assert module._format_datetime(aware, "%Y") == "2026"


def test_safe_redirect_and_save_formulario_with_user(mocker):
    req = SimpleNamespace(
        get_full_path=lambda: "/a", user=SimpleNamespace(is_authenticated=True)
    )
    admision = SimpleNamespace(pk=7)

    safe = mocker.patch(
        "admisiones.services.legales_service.safe_redirect", return_value="ok"
    )
    rev = mocker.patch(
        "admisiones.services.legales_service.reverse", return_value="/dest"
    )
    assert module.LegalesService._safe_redirect(req, admision) == "ok"
    rev.assert_called_once()
    safe.assert_called_once()

    inst = SimpleNamespace(admision=None, creado_por=None, save=mocker.Mock())
    form = mocker.Mock()
    form.save.return_value = inst
    req2 = SimpleNamespace(user=SimpleNamespace(is_authenticated=True))
    got = module.LegalesService._save_formulario_with_user(form, admision, req2)
    assert got is inst
    assert inst.admision is admision
    assert inst.creado_por is req2.user
    inst.save.assert_called_once()


def test_reset_dictamen_flow_variants(mocker):
    del_conv = mocker.patch(
        "admisiones.services.legales_service.FormularioProyectoDeConvenio.objects.filter"
    )
    del_disp = mocker.patch(
        "admisiones.services.legales_service.FormularioProyectoDisposicion.objects.filter"
    )
    del_conv.return_value.delete.return_value = None
    del_disp.return_value.delete.return_value = None

    adm = SimpleNamespace(
        dictamen_motivo="observacion en proyecto de convenio",
        intervencion_juridicos="x",
        rechazo_juridicos_motivo="y",
        save=mocker.Mock(),
    )
    module.LegalesService._reset_dictamen_flow(adm)
    assert adm.estado_legales == "Expediente Agregado"

    adm2 = SimpleNamespace(
        dictamen_motivo="observacion en proyecto de disposicion",
        save=mocker.Mock(),
    )
    module.LegalesService._reset_dictamen_flow(adm2)
    assert adm2.estado_legales == "IF Convenio Asignado"


def test_get_botones_disponibles_core_branches():
    adm = SimpleNamespace(
        legales_num_if=None,
        enviado_legales=True,
        estado_legales="Enviado a Legales",
        admisiones_proyecto_convenio=SimpleNamespace(first=lambda: SimpleNamespace()),
        admisiones_proyecto_disposicion=SimpleNamespace(
            first=lambda: SimpleNamespace()
        ),
        rechazo_juridicos_motivo=None,
        dictamen_motivo=None,
        complementario_solicitado=False,
        numero_disposicion=None,
        informe_sga=False,
        numero_convenio=None,
        enviada_a_archivo=False,
    )
    botones = module.LegalesService.get_botones_disponibles(adm)
    assert "rectificar" in botones
    assert "agregar_expediente" in botones

    adm.estado_legales = "Expediente Agregado"
    adm.enviado_legales = False
    botones = module.LegalesService.get_botones_disponibles(adm)
    assert "formulario_convenio" in botones

    adm.estado_legales = "Juridicos: Rechazado"
    adm.rechazo_juridicos_motivo = "providencia"
    botones = module.LegalesService.get_botones_disponibles(adm)
    assert "reinicio_expediente" in botones


def test_actualizar_estado_por_accion(mocker):
    adm = SimpleNamespace(intervencion_juridicos="validado", save=mocker.Mock())
    module.LegalesService.actualizar_estado_por_accion(adm, "intervencion_juridicos")
    assert adm.estado_legales == "Juridicos: Validado"

    adm2 = SimpleNamespace(intervencion_juridicos="rechazado", save=mocker.Mock())
    module.LegalesService.actualizar_estado_por_accion(adm2, "intervencion_juridicos")
    assert adm2.estado_legales == "Juridicos: Rechazado"

    adm3 = SimpleNamespace(save=mocker.Mock())
    module.LegalesService.actualizar_estado_por_accion(adm3, "if_disposicion")
    assert adm3.estado_legales == "IF Disposición Asignado"


def test_enviar_a_rectificar_success_error_and_exception(mocker):
    req = SimpleNamespace(POST={}, user=SimpleNamespace(), get_full_path=lambda: "/x")
    adm = SimpleNamespace(pk=1, estado_id=1, observaciones="", save=mocker.Mock())

    form = mocker.Mock()
    form.is_valid.return_value = True
    form.cleaned_data = {"observaciones": "obs"}
    mocker.patch(
        "admisiones.services.legales_service.LegalesRectificarForm", return_value=form
    )
    update = mocker.patch.object(module.LegalesService, "actualizar_estado_por_accion")
    ok_redirect = mocker.patch(
        "admisiones.services.legales_service.redirect", return_value="r"
    )
    mocker.patch("admisiones.services.legales_service.messages.success")

    assert module.LegalesService.enviar_a_rectificar(req, adm) == "r"
    update.assert_called_once_with(adm, "rectificar")
    ok_redirect.assert_called()

    form2 = mocker.Mock(is_valid=mocker.Mock(return_value=False))
    mocker.patch(
        "admisiones.services.legales_service.LegalesRectificarForm", return_value=form2
    )
    mocker.patch("admisiones.services.legales_service.messages.error")
    assert module.LegalesService.enviar_a_rectificar(req, adm) == "r"

    mocker.patch(
        "admisiones.services.legales_service.LegalesRectificarForm",
        side_effect=RuntimeError("boom"),
    )
    assert module.LegalesService.enviar_a_rectificar(req, adm) == "r"


def test_guardar_actions_common_flows(mocker):
    """Guard methods should branch on form validity and keep redirect contract."""
    req = SimpleNamespace(
        POST={},
        FILES={},
        user=SimpleNamespace(is_authenticated=True),
        get_full_path=lambda: "/x",
    )
    adm = SimpleNamespace(
        pk=9,
        informe_sga=False,
        numero_disposicion=None,
        numero_convenio=None,
        admisiones_proyecto_convenio=SimpleNamespace(first=lambda: SimpleNamespace()),
        admisiones_proyecto_disposicion=SimpleNamespace(
            first=lambda: SimpleNamespace()
        ),
        save=mocker.Mock(),
    )

    mocker.patch("admisiones.services.legales_service.messages.success")
    mocker.patch("admisiones.services.legales_service.messages.error")
    mocker.patch("admisiones.services.legales_service.redirect", return_value="r")
    mocker.patch.object(module.LegalesService, "_safe_redirect", return_value="sr")
    upd = mocker.patch.object(module.LegalesService, "actualizar_estado_por_accion")
    save_with_user = mocker.patch.object(
        module.LegalesService, "_save_formulario_with_user"
    )

    # guardar_legales_num_if
    form = mocker.Mock(is_valid=mocker.Mock(return_value=True), save=mocker.Mock())
    mocker.patch(
        "admisiones.services.legales_service.LegalesNumIFForm", return_value=form
    )
    assert module.LegalesService.guardar_legales_num_if(req, adm) == "sr"

    # guardar_intervencion_juridicos
    adm.intervencion_juridicos = "validado"
    adm.rechazo_juridicos_motivo = None
    adm.dictamen_motivo = None
    form2 = mocker.Mock(is_valid=mocker.Mock(return_value=True), save=mocker.Mock())
    mocker.patch(
        "admisiones.services.legales_service.IntervencionJuridicosForm",
        return_value=form2,
    )
    assert module.LegalesService.guardar_intervencion_juridicos(req, adm) == "r"

    # guardar_informe_sga toggles boolean
    assert module.LegalesService.guardar_informe_sga(req, adm) == "r"

    # guardar_convenio / guardar_disposicion
    form3 = mocker.Mock(
        is_valid=mocker.Mock(return_value=True), save=mocker.Mock(), errors={}
    )
    mocker.patch("admisiones.services.legales_service.ConvenioForm", return_value=form3)
    assert module.LegalesService.guardar_convenio(req, adm) == "r"

    form4 = mocker.Mock(
        is_valid=mocker.Mock(return_value=True), save=mocker.Mock(), errors={}
    )
    mocker.patch(
        "admisiones.services.legales_service.DisposicionForm", return_value=form4
    )
    assert module.LegalesService.guardar_disposicion(req, adm) == "r"

    # guardar_convenio_num_if / guardar_dispo_num_if
    form5 = mocker.Mock(is_valid=mocker.Mock(return_value=True))
    mocker.patch(
        "admisiones.services.legales_service.ConvenioNumIFFORM", return_value=form5
    )
    assert module.LegalesService.guardar_convenio_num_if(req, adm) == "sr"

    form6 = mocker.Mock(is_valid=mocker.Mock(return_value=True))
    mocker.patch(
        "admisiones.services.legales_service.DisposicionNumIFFORM", return_value=form6
    )
    assert module.LegalesService.guardar_dispo_num_if(req, adm) == "sr"

    # guardar_reinicio_expediente
    reinicio_obj = SimpleNamespace(enviada_a_archivo=False, save=mocker.Mock())
    form7 = mocker.Mock(
        is_valid=mocker.Mock(return_value=True),
        save=mocker.Mock(return_value=reinicio_obj),
    )
    mocker.patch(
        "admisiones.services.legales_service.ReinicioExpedienteForm", return_value=form7
    )
    assert module.LegalesService.guardar_reinicio_expediente(req, adm) == "sr"

    assert upd.called
    assert save_with_user.called


def test_revisar_if_limpiar_observaciones_and_validar(mocker):
    """Complementary-review and validation helpers should manage state transitions."""
    req = SimpleNamespace(
        POST={"accion_complementario": "validar"},
        user=SimpleNamespace(is_authenticated=True),
        get_full_path=lambda: "/x",
    )
    adm = SimpleNamespace(
        pk=5,
        estado_legales="X",
        complementario_solicitado=True,
        observaciones_informe_tecnico_complementario="obs",
        observaciones="",
        legales_num_if="if",
        save=mocker.Mock(),
    )

    info = SimpleNamespace(
        estado="enviado_validacion", observaciones_legales="", save=mocker.Mock()
    )
    mocker.patch("admisiones.services.legales_service.messages.success")
    mocker.patch("admisiones.services.legales_service.messages.error")
    mocker.patch("admisiones.services.legales_service.redirect", return_value="r")
    mocker.patch.object(module.LegalesService, "_safe_redirect", return_value="sr")

    mocker.patch(
        "admisiones.services.legales_service.InformeComplementario.objects.filter",
        return_value=SimpleNamespace(first=lambda: info),
    )
    mocker.patch(
        "admisiones.services.informes_service.InformeService.generar_y_guardar_pdf_complementario",
        return_value=SimpleNamespace(),
    )
    assert module.LegalesService.revisar_informe_complementario(req, adm) == "r"

    req_rect = SimpleNamespace(
        POST={
            "accion_complementario": "rectificar",
            "observaciones_complementario": "detalle",
        },
        user=req.user,
        get_full_path=req.get_full_path,
    )
    assert module.LegalesService.revisar_informe_complementario(req_rect, adm) == "r"

    # guardar_if_informe_complementario
    pdf = SimpleNamespace(numero_if=None, save=mocker.Mock())
    mocker.patch(
        "admisiones.models.admisiones.InformeTecnicoComplementarioPDF.objects.filter",
        return_value=SimpleNamespace(first=lambda: pdf),
    )
    limpiar = mocker.patch.object(module.LegalesService, "_limpiar_flujo_anterior")
    req_if = SimpleNamespace(
        POST={"numero_if_complementario": "IF-1"}, get_full_path=lambda: "/x"
    )
    assert module.LegalesService.guardar_if_informe_complementario(req_if, adm) == "sr"
    assert limpiar.called

    # observaciones informe complementario
    comp = SimpleNamespace(complementario_solicitado=False, save=mocker.Mock())
    form_obs = mocker.Mock(
        is_valid=mocker.Mock(return_value=True), save=mocker.Mock(return_value=comp)
    )
    mocker.patch(
        "admisiones.services.legales_service.SolicitarInformeComplementarioForm",
        return_value=form_obs,
    )
    upd = mocker.patch.object(module.LegalesService, "actualizar_estado_por_accion")
    req_obs = SimpleNamespace(POST={}, get_full_path=lambda: "/x")
    assert (
        module.LegalesService.guardar_observaciones_informe_complementario(req_obs, adm)
        == "sr"
    )
    assert upd.called

    # validar juridicos
    mocker.patch(
        "admisiones.services.legales_service.FormularioProyectoDisposicion.objects.filter",
        return_value=SimpleNamespace(exists=lambda: True),
    )
    mocker.patch(
        "admisiones.services.legales_service.FormularioProyectoDeConvenio.objects.filter",
        return_value=SimpleNamespace(exists=lambda: True),
    )
    assert module.LegalesService.validar_juridicos(req_obs, adm) == "sr"


def test_limpiar_flujo_anterior_resets_fields(mocker):
    """Legacy flow cleanup should clear juridical/complementary fields."""
    adm = SimpleNamespace(
        pk=6,
        intervencion_juridicos="x",
        rechazo_juridicos_motivo="y",
        dictamen_motivo="z",
        complementario_solicitado=True,
        observaciones_informe_tecnico_complementario="obs",
        estado_legales="otro",
        save=mocker.Mock(),
    )
    mocker.patch(
        "admisiones.services.legales_service.FormularioProyectoDeConvenio.objects.filter",
        return_value=SimpleNamespace(delete=mocker.Mock()),
    )
    mocker.patch(
        "admisiones.services.legales_service.FormularioProyectoDisposicion.objects.filter",
        return_value=SimpleNamespace(delete=mocker.Mock()),
    )

    module.LegalesService._limpiar_flujo_anterior(adm)
    assert adm.complementario_solicitado is False
    assert adm.estado_legales == "Informe Complementario: Validado"


def test_table_data_filtering_and_post_router(mocker):
    """List/table helpers and POST router should dispatch to expected handlers."""
    adm = SimpleNamespace(
        pk=1,
        tipo="incorporacion",
        get_tipo_display=lambda: "Incorporación",
        comedor=SimpleNamespace(
            id=10,
            nombre="Comedor",
            provincia="Buenos Aires",
            dupla="Dupla 1",
            organizacion=SimpleNamespace(nombre="Org"),
        ),
        tipo_convenio=SimpleNamespace(nombre="Tipo"),
        num_expediente="EX-1",
        num_if="IF-1",
        estado_legales="Enviado a Legales",
        get_estado_legales_display=lambda: "Enviado",
        modificado=datetime(2026, 1, 2, 3, 4),
        convenio_numero=None,
    )
    mocker.patch(
        "admisiones.services.legales_service.reverse",
        side_effect=lambda name, args=None, kwargs=None: f"/{name}/{(args or [kwargs.get('pk')])[0]}",
    )
    rows = module.LegalesService.get_admisiones_legales_table_data([adm])
    assert rows and rows[0]["cells"][0]["content"] == "10"

    # filtering happy path
    qs = SimpleNamespace(
        select_related=lambda *a, **k: qs,
        filter=lambda *a, **k: qs,
        none=lambda: "none",
    )
    mocker.patch(
        "admisiones.services.legales_service.Admision.objects.filter", return_value=qs
    )
    mocker.patch(
        "users.services.UserPermissionService.get_coordinador_duplas",
        return_value=(True, [1]),
    )
    mocker.patch(
        "admisiones.services.legales_service.LEGALES_ADVANCED_FILTER.filter_queryset",
        return_value=qs,
    )
    out = module.LegalesService.get_admisiones_legales_filtradas(
        {"busqueda": "x"}, user=SimpleNamespace(is_superuser=False)
    )
    assert out is qs

    # post router
    req = SimpleNamespace(POST={"btnConvenio": "1"})
    mocker.patch.object(module.LegalesService, "guardar_convenio", return_value="ok")
    assert (
        module.LegalesService.procesar_post_legales(req, SimpleNamespace(pk=1)) == "ok"
    )


def test_procesar_post_legales_cubre_botones_restantes(mocker):
    """Enruta correctamente cada botón de POST hacia su handler."""
    adm = SimpleNamespace(pk=1)
    handlers = {
        "btnLegalesNumIF": "guardar_legales_num_if",
        "BtnIntervencionJuridicos": "guardar_intervencion_juridicos",
        "btnDisposicion": "guardar_disposicion",
        "btnConvenioNumIF": "guardar_convenio_num_if",
        "btnDispoNumIF": "guardar_dispo_num_if",
        "btnReinicioExpediente": "guardar_reinicio_expediente",
        "btnInformeComplementario": "guardar_observaciones_informe_complementario",
        "btnRevisarInformeComplementario": "revisar_informe_complementario",
        "btnIFInformeComplementario": "guardar_if_informe_complementario",
        "ValidacionJuridicos": "validar_juridicos",
        "btnRESO": "guardar_formulario_reso",
        "btnProyectoConvenio": "guardar_formulario_proyecto_convenio",
        "btnObservaciones": "enviar_a_rectificar",
    }
    for post_key, method_name in handlers.items():
        expected = f"ok-{post_key}"
        mocked = mocker.patch.object(
            module.LegalesService, method_name, return_value=expected
        )
        out = module.LegalesService.procesar_post_legales(
            SimpleNamespace(POST={post_key: "1"}), adm
        )
        assert out == expected
        mocked.assert_called_once()


def test_procesar_post_legales_default_and_exception(mocker):
    """Sin botón redirige y ante excepción muestra error controlado."""
    adm = SimpleNamespace(pk=2)
    red = mocker.patch(
        "admisiones.services.legales_service.redirect", return_value="redir"
    )
    msg = mocker.patch("admisiones.services.legales_service.messages.error")

    assert (
        module.LegalesService.procesar_post_legales(SimpleNamespace(POST={}), adm)
        == "redir"
    )

    mocker.patch.object(
        module.LegalesService, "guardar_convenio", side_effect=RuntimeError("boom")
    )
    out = module.LegalesService.procesar_post_legales(
        SimpleNamespace(POST={"btnConvenio": "1"}), adm
    )
    assert out == "redir"
    assert red.called
    assert msg.called


def test_guardar_formulario_proyecto_convenio_success_y_docx_fallback(mocker):
    """Guarda convenio generando PDF y soporta fallback cuando DOCX falla."""
    req = SimpleNamespace(
        POST={}, user=SimpleNamespace(is_authenticated=True), get_full_path=lambda: "/x"
    )
    adm = SimpleNamespace(
        pk=10,
        tipo="incorporacion",
        tipo_convenio=SimpleNamespace(nombre="Personeria Juridica"),
        comedor=SimpleNamespace(nombre="Comedor Uno"),
    )

    form_obj = _build_formulario_fake(mocker)
    form = mocker.Mock(
        is_valid=mocker.Mock(return_value=True), save=mocker.Mock(return_value=form_obj)
    )
    mocker.patch(
        "admisiones.services.legales_service.FormularioProyectoDeConvenio.objects.filter",
        return_value=SimpleNamespace(first=lambda: None),
    )
    mocker.patch(
        "admisiones.services.legales_service.ProyectoConvenioForm", return_value=form
    )
    mocker.patch(
        "admisiones.services.legales_service.InformeTecnico.objects.filter",
        return_value=SimpleNamespace(
            order_by=lambda *_: SimpleNamespace(first=lambda: None)
        ),
    )
    mocker.patch(
        "admisiones.services.legales_service.render_to_string",
        return_value="<html>ok</html>",
    )
    mocker.patch(
        "admisiones.services.legales_service.HTML",
        return_value=SimpleNamespace(write_pdf=lambda: b"pdf"),
    )
    mocker.patch(
        "admisiones.services.legales_service.slugify", return_value="convenio-test"
    )
    mocker.patch(
        "admisiones.services.legales_service.transaction.atomic",
        return_value=nullcontext(),
    )
    mocker.patch.object(module.LegalesService, "actualizar_estado_por_accion")
    mocker.patch.object(module.LegalesService, "_safe_redirect", return_value="sr")
    success = mocker.patch("admisiones.services.legales_service.messages.success")

    mocker.patch(
        "admisiones.services.legales_service.DocumentTemplateService.generar_docx",
        return_value=BytesIO(b"docx"),
    )
    out = module.LegalesService.guardar_formulario_proyecto_convenio(req, adm)
    assert out == "sr"
    assert form_obj.archivo.save.called
    assert form_obj.archivo_docx.save.called

    success.reset_mock()
    mocker.patch(
        "admisiones.services.legales_service.DocumentTemplateService.generar_docx",
        side_effect=RuntimeError("no-docx"),
    )
    out2 = module.LegalesService.guardar_formulario_proyecto_convenio(req, adm)
    assert out2 == "sr"
    assert success.called


def test_guardar_formulario_proyecto_convenio_invalid_and_exception(mocker):
    """Cuando el formulario es inválido o falla, retorna safe redirect con error."""
    req = SimpleNamespace(
        POST={}, user=SimpleNamespace(is_authenticated=True), get_full_path=lambda: "/x"
    )
    adm = SimpleNamespace(
        pk=11,
        tipo="incorporacion",
        tipo_convenio=SimpleNamespace(nombre="Base"),
        comedor=None,
    )

    invalid_form = mocker.Mock(is_valid=mocker.Mock(return_value=False))
    mocker.patch(
        "admisiones.services.legales_service.FormularioProyectoDeConvenio.objects.filter",
        return_value=SimpleNamespace(first=lambda: None),
    )
    mocker.patch(
        "admisiones.services.legales_service.ProyectoConvenioForm",
        return_value=invalid_form,
    )
    mocker.patch.object(module.LegalesService, "_safe_redirect", return_value="sr")
    red = mocker.patch("admisiones.services.legales_service.redirect", return_value="r")
    error = mocker.patch("admisiones.services.legales_service.messages.error")
    assert module.LegalesService.guardar_formulario_proyecto_convenio(req, adm) == "r"
    assert red.called
    assert error.called

    mocker.patch(
        "admisiones.services.legales_service.ProyectoConvenioForm",
        side_effect=RuntimeError("boom"),
    )
    assert module.LegalesService.guardar_formulario_proyecto_convenio(req, adm) == "sr"


def test_guardar_formulario_reso_success_and_invalid(mocker):
    """Guarda formulario de disposición con generación de PDF/DOCX y cubre inválido."""
    req = SimpleNamespace(POST={}, user=SimpleNamespace(is_authenticated=True))
    adm = SimpleNamespace(
        pk=12,
        tipo="renovacion",
        comedor=SimpleNamespace(nombre="Comedor Dos"),
        admisiones_proyecto_convenio=SimpleNamespace(
            first=lambda: SimpleNamespace(numero_if="IF-9")
        ),
    )

    form_obj = _build_formulario_fake(mocker)
    form = mocker.Mock(
        is_valid=mocker.Mock(return_value=True), save=mocker.Mock(return_value=form_obj)
    )
    mocker.patch(
        "admisiones.services.legales_service.transaction.atomic",
        return_value=nullcontext(),
    )
    mocker.patch(
        "admisiones.services.legales_service.FormularioProyectoDisposicion.objects.filter",
        return_value=SimpleNamespace(first=lambda: None),
    )
    mocker.patch(
        "admisiones.services.legales_service.ProyectoDisposicionForm", return_value=form
    )
    mocker.patch(
        "admisiones.services.legales_service.InformeTecnico.objects.filter",
        return_value=SimpleNamespace(
            order_by=lambda *_: SimpleNamespace(first=lambda: None)
        ),
    )
    mocker.patch(
        "admisiones.services.legales_service.FormularioProyectoDeConvenio.objects.filter",
        return_value=SimpleNamespace(first=lambda: SimpleNamespace(numero_if="IF-10")),
    )
    mocker.patch(
        "admisiones.services.legales_service.render_to_string",
        return_value="<html>ok</html>",
    )
    mocker.patch(
        "admisiones.services.legales_service.HTML",
        return_value=SimpleNamespace(write_pdf=lambda: b"pdf"),
    )
    mocker.patch(
        "admisiones.services.legales_service.DocumentTemplateService.generar_docx",
        return_value=BytesIO(b"docx"),
    )
    mocker.patch(
        "admisiones.services.legales_service.slugify", return_value="dispo-test"
    )
    mocker.patch.object(module.LegalesService, "actualizar_estado_por_accion")
    mocker.patch("admisiones.services.legales_service.messages.success")
    mocker.patch("admisiones.services.legales_service.messages.error")
    red = mocker.patch("admisiones.services.legales_service.redirect", return_value="r")
    assert module.LegalesService.guardar_formulario_reso(req, adm) == "r"
    assert form_obj.archivo.save.called
    assert form_obj.archivo_docx.save.called
    assert red.called

    invalid = mocker.Mock(is_valid=mocker.Mock(return_value=False))
    mocker.patch(
        "admisiones.services.legales_service.ProyectoDisposicionForm",
        return_value=invalid,
    )
    assert module.LegalesService.guardar_formulario_reso(req, adm) == "r"


def test_get_legales_context_and_helpers(mocker):
    """Construye contexto legal, cubre helper de informe y generación de documentos."""
    adm = SimpleNamespace(
        pk=20,
        tipo_convenio=object(),
        historial=SimpleNamespace(
            all=lambda: _Chain(
                [
                    SimpleNamespace(
                        fecha=datetime(2026, 1, 1, 10, 0),
                        campo="x",
                        valor_nuevo="True",
                        usuario=SimpleNamespace(username="u"),
                    )
                ]
            )
        ),
        historial_estados=SimpleNamespace(
            all=lambda: _Chain(
                [
                    SimpleNamespace(
                        fecha=datetime(2026, 1, 2, 10, 0),
                        estado_anterior="A Rectificar",
                        estado_nuevo="Pendiente de Validacion",
                        usuario=SimpleNamespace(username="u"),
                    )
                ]
            )
        ),
        admisiones_proyecto_disposicion=SimpleNamespace(first=lambda: None),
        admisiones_proyecto_convenio=SimpleNamespace(first=lambda: None),
        informe_pdf=None,
        tipo_informe="base",
    )
    req = SimpleNamespace(GET={"historial_page": "1", "historial_estados_page": "1"})

    docs = [SimpleNamespace(id=1, nombre="Doc 1")]
    archs = [
        SimpleNamespace(
            documentacion_id=1,
            archivo=SimpleNamespace(url="/a.pdf"),
            id=1,
            nombre_personalizado=None,
        ),
        SimpleNamespace(
            documentacion_id=None,
            archivo=SimpleNamespace(url="/b.pdf"),
            id=2,
            nombre_personalizado="Personalizado",
        ),
    ]
    expedientes = _Chain(
        [
            SimpleNamespace(tipo="Informe SGA", value="v1"),
            SimpleNamespace(tipo="Disposición", value="v2"),
        ]
    )

    mocker.patch(
        "admisiones.services.legales_service.Documentacion.objects.filter",
        return_value=SimpleNamespace(distinct=lambda: docs),
    )
    mocker.patch.object(
        module.LegalesService,
        "get_informe_por_tipo_convenio",
        return_value=SimpleNamespace(pk=1),
    )
    mocker.patch(
        "admisiones.services.legales_service.ArchivoAdmision.objects.filter",
        return_value=archs,
    )
    mocker.patch(
        "admisiones.services.legales_service.InformeComplementario.objects.filter",
        return_value=SimpleNamespace(order_by=lambda *_: []),
    )
    mocker.patch(
        "admisiones.models.admisiones.InformeTecnicoComplementarioPDF.objects.filter",
        return_value=SimpleNamespace(first=lambda: None),
    )
    mocker.patch(
        "admisiones.services.legales_service.DocumentosExpediente.objects.filter",
        return_value=expedientes,
    )
    mocker.patch(
        "admisiones.services.legales_service.ProyectoDisposicionForm",
        return_value="fdis",
    )
    mocker.patch(
        "admisiones.services.legales_service.DisposicionNumIFFORM",
        return_value="fdisif",
    )
    mocker.patch(
        "admisiones.services.legales_service.ProyectoConvenioForm", return_value="fconv"
    )
    mocker.patch(
        "admisiones.services.legales_service.ConvenioNumIFFORM", return_value="fconvif"
    )
    mocker.patch(
        "admisiones.services.legales_service.LegalesNumIFForm", return_value="flnum"
    )
    mocker.patch(
        "admisiones.services.legales_service.DocumentosExpedienteForm",
        return_value="fdoc",
    )
    mocker.patch(
        "admisiones.services.legales_service.IntervencionJuridicosForm",
        return_value="fint",
    )
    mocker.patch(
        "admisiones.services.legales_service.InformeSGAForm", return_value="fsga"
    )
    mocker.patch("admisiones.services.legales_service.ConvenioForm", return_value="fco")
    mocker.patch(
        "admisiones.services.legales_service.DisposicionForm", return_value="fdi"
    )
    mocker.patch(
        "admisiones.services.legales_service.ReinicioExpedienteForm", return_value="fre"
    )
    mocker.patch(
        "admisiones.services.legales_service.SolicitarInformeComplementarioForm",
        return_value="fsol",
    )
    mocker.patch.object(
        module.LegalesService, "get_botones_disponibles", return_value=["x"]
    )

    ctx = module.LegalesService.get_legales_context(adm, req)
    assert ctx["documentos"]
    assert ctx["botones_disponibles"] == ["x"]


def test_legales_informe_y_documentos_helpers(mocker):
    """Resuelve helper de informe por tipo y genera DOCX de convenio/disposición."""
    adm = SimpleNamespace(pk=30, tipo_informe="base")

    mocker.patch(
        "admisiones.services.legales_service.InformeTecnico.objects.filter",
        return_value=SimpleNamespace(first=lambda: "ok"),
    )
    assert module.LegalesService.get_informe_por_tipo_convenio(adm) == "ok"
    assert (
        module.LegalesService.get_informe_por_tipo_convenio(
            SimpleNamespace(tipo_informe=None, pk=99)
        )
        is None
    )

    mocker.patch(
        "admisiones.services.legales_service.TextFormatterService.preparar_contexto_proyecto_convenio",
        return_value={},
    )
    mocker.patch(
        "admisiones.services.legales_service.DocumentTemplateService.generar_docx",
        return_value=BytesIO(b"x"),
    )
    out_doc = module.LegalesService.generar_documento_convenio(SimpleNamespace(id=1))
    assert out_doc is not None

    mocker.patch(
        "admisiones.services.legales_service.TextFormatterService.preparar_contexto_proyecto_disposicion",
        return_value={},
    )
    out_doc2 = module.LegalesService.generar_documento_disposicion(
        SimpleNamespace(id=2)
    )
    assert out_doc2 is not None
