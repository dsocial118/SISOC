"""Tests for test legales service unit."""

from datetime import datetime
from types import SimpleNamespace

from django.utils import timezone

from admisiones.services import legales_service as module


def test_normalizar_and_format_datetime():
    assert module.normalizar(" ÁéÍ ") == "aei"
    assert module.normalizar("") == ""

    assert module._format_datetime(None, "%d/%m/%Y") == "-"
    naive = datetime(2026, 1, 2, 3, 4)
    assert module._format_datetime(naive, "%d/%m/%Y") == "02/01/2026"

    aware = timezone.make_aware(datetime(2026, 1, 2, 3, 4))
    assert module._format_datetime(aware, "%Y") == "2026"


def test_safe_redirect_and_save_formulario_with_user(mocker):
    req = SimpleNamespace(get_full_path=lambda: "/a", user=SimpleNamespace(is_authenticated=True))
    admision = SimpleNamespace(pk=7)

    safe = mocker.patch("admisiones.services.legales_service.safe_redirect", return_value="ok")
    rev = mocker.patch("admisiones.services.legales_service.reverse", return_value="/dest")
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
    del_conv = mocker.patch("admisiones.services.legales_service.FormularioProyectoDeConvenio.objects.filter")
    del_disp = mocker.patch("admisiones.services.legales_service.FormularioProyectoDisposicion.objects.filter")
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
        admisiones_proyecto_disposicion=SimpleNamespace(first=lambda: SimpleNamespace()),
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
    mocker.patch("admisiones.services.legales_service.LegalesRectificarForm", return_value=form)
    update = mocker.patch.object(module.LegalesService, "actualizar_estado_por_accion")
    ok_redirect = mocker.patch("admisiones.services.legales_service.redirect", return_value="r")
    mocker.patch("admisiones.services.legales_service.messages.success")

    assert module.LegalesService.enviar_a_rectificar(req, adm) == "r"
    update.assert_called_once_with(adm, "rectificar")
    ok_redirect.assert_called()

    form2 = mocker.Mock(is_valid=mocker.Mock(return_value=False))
    mocker.patch("admisiones.services.legales_service.LegalesRectificarForm", return_value=form2)
    mocker.patch("admisiones.services.legales_service.messages.error")
    assert module.LegalesService.enviar_a_rectificar(req, adm) == "r"

    mocker.patch("admisiones.services.legales_service.LegalesRectificarForm", side_effect=RuntimeError("boom"))
    assert module.LegalesService.enviar_a_rectificar(req, adm) == "r"


def test_guardar_actions_common_flows(mocker):
    """Guard methods should branch on form validity and keep redirect contract."""
    req = SimpleNamespace(POST={}, FILES={}, user=SimpleNamespace(is_authenticated=True), get_full_path=lambda: "/x")
    adm = SimpleNamespace(
        pk=9,
        informe_sga=False,
        numero_disposicion=None,
        numero_convenio=None,
        admisiones_proyecto_convenio=SimpleNamespace(first=lambda: SimpleNamespace()),
        admisiones_proyecto_disposicion=SimpleNamespace(first=lambda: SimpleNamespace()),
        save=mocker.Mock(),
    )

    mocker.patch("admisiones.services.legales_service.messages.success")
    mocker.patch("admisiones.services.legales_service.messages.error")
    mocker.patch("admisiones.services.legales_service.redirect", return_value="r")
    mocker.patch.object(module.LegalesService, "_safe_redirect", return_value="sr")
    upd = mocker.patch.object(module.LegalesService, "actualizar_estado_por_accion")
    save_with_user = mocker.patch.object(module.LegalesService, "_save_formulario_with_user")

    # guardar_legales_num_if
    form = mocker.Mock(is_valid=mocker.Mock(return_value=True), save=mocker.Mock())
    mocker.patch("admisiones.services.legales_service.LegalesNumIFForm", return_value=form)
    assert module.LegalesService.guardar_legales_num_if(req, adm) == "sr"

    # guardar_intervencion_juridicos
    adm.intervencion_juridicos = "validado"
    adm.rechazo_juridicos_motivo = None
    adm.dictamen_motivo = None
    form2 = mocker.Mock(is_valid=mocker.Mock(return_value=True), save=mocker.Mock())
    mocker.patch("admisiones.services.legales_service.IntervencionJuridicosForm", return_value=form2)
    assert module.LegalesService.guardar_intervencion_juridicos(req, adm) == "r"

    # guardar_informe_sga toggles boolean
    assert module.LegalesService.guardar_informe_sga(req, adm) == "r"

    # guardar_convenio / guardar_disposicion
    form3 = mocker.Mock(is_valid=mocker.Mock(return_value=True), save=mocker.Mock(), errors={})
    mocker.patch("admisiones.services.legales_service.ConvenioForm", return_value=form3)
    assert module.LegalesService.guardar_convenio(req, adm) == "r"

    form4 = mocker.Mock(is_valid=mocker.Mock(return_value=True), save=mocker.Mock(), errors={})
    mocker.patch("admisiones.services.legales_service.DisposicionForm", return_value=form4)
    assert module.LegalesService.guardar_disposicion(req, adm) == "r"

    # guardar_convenio_num_if / guardar_dispo_num_if
    form5 = mocker.Mock(is_valid=mocker.Mock(return_value=True))
    mocker.patch("admisiones.services.legales_service.ConvenioNumIFFORM", return_value=form5)
    assert module.LegalesService.guardar_convenio_num_if(req, adm) == "sr"

    form6 = mocker.Mock(is_valid=mocker.Mock(return_value=True))
    mocker.patch("admisiones.services.legales_service.DisposicionNumIFFORM", return_value=form6)
    assert module.LegalesService.guardar_dispo_num_if(req, adm) == "sr"

    # guardar_reinicio_expediente
    reinicio_obj = SimpleNamespace(enviada_a_archivo=False, save=mocker.Mock())
    form7 = mocker.Mock(is_valid=mocker.Mock(return_value=True), save=mocker.Mock(return_value=reinicio_obj))
    mocker.patch("admisiones.services.legales_service.ReinicioExpedienteForm", return_value=form7)
    assert module.LegalesService.guardar_reinicio_expediente(req, adm) == "sr"

    assert upd.called
    assert save_with_user.called


def test_revisar_if_limpiar_observaciones_and_validar(mocker):
    """Complementary-review and validation helpers should manage state transitions."""
    req = SimpleNamespace(POST={"accion_complementario": "validar"}, user=SimpleNamespace(is_authenticated=True), get_full_path=lambda: "/x")
    adm = SimpleNamespace(
        pk=5,
        estado_legales="X",
        complementario_solicitado=True,
        observaciones_informe_tecnico_complementario="obs",
        observaciones="",
        legales_num_if="if",
        save=mocker.Mock(),
    )

    info = SimpleNamespace(estado="enviado_validacion", observaciones_legales="", save=mocker.Mock())
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

    req_rect = SimpleNamespace(POST={"accion_complementario": "rectificar", "observaciones_complementario": "detalle"}, user=req.user, get_full_path=req.get_full_path)
    assert module.LegalesService.revisar_informe_complementario(req_rect, adm) == "r"

    # guardar_if_informe_complementario
    pdf = SimpleNamespace(numero_if=None, save=mocker.Mock())
    mocker.patch(
        "admisiones.models.admisiones.InformeTecnicoComplementarioPDF.objects.filter",
        return_value=SimpleNamespace(first=lambda: pdf),
    )
    limpiar = mocker.patch.object(module.LegalesService, "_limpiar_flujo_anterior")
    req_if = SimpleNamespace(POST={"numero_if_complementario": "IF-1"}, get_full_path=lambda: "/x")
    assert module.LegalesService.guardar_if_informe_complementario(req_if, adm) == "sr"
    assert limpiar.called

    # observaciones informe complementario
    comp = SimpleNamespace(complementario_solicitado=False, save=mocker.Mock())
    form_obs = mocker.Mock(is_valid=mocker.Mock(return_value=True), save=mocker.Mock(return_value=comp))
    mocker.patch("admisiones.services.legales_service.SolicitarInformeComplementarioForm", return_value=form_obs)
    upd = mocker.patch.object(module.LegalesService, "actualizar_estado_por_accion")
    req_obs = SimpleNamespace(POST={}, get_full_path=lambda: "/x")
    assert module.LegalesService.guardar_observaciones_informe_complementario(req_obs, adm) == "sr"
    assert upd.called

    # validar juridicos
    mocker.patch("admisiones.services.legales_service.FormularioProyectoDisposicion.objects.filter", return_value=SimpleNamespace(exists=lambda: True))
    mocker.patch("admisiones.services.legales_service.FormularioProyectoDeConvenio.objects.filter", return_value=SimpleNamespace(exists=lambda: True))
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
    mocker.patch("admisiones.services.legales_service.FormularioProyectoDeConvenio.objects.filter", return_value=SimpleNamespace(delete=mocker.Mock()))
    mocker.patch("admisiones.services.legales_service.FormularioProyectoDisposicion.objects.filter", return_value=SimpleNamespace(delete=mocker.Mock()))

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
    mocker.patch("admisiones.services.legales_service.reverse", side_effect=lambda name, args=None, kwargs=None: f"/{name}/{(args or [kwargs.get('pk')])[0]}")
    rows = module.LegalesService.get_admisiones_legales_table_data([adm])
    assert rows and rows[0]["cells"][0]["content"] == "10"

    # filtering happy path
    qs = SimpleNamespace(
        select_related=lambda *a, **k: qs,
        filter=lambda *a, **k: qs,
        none=lambda: "none",
    )
    mocker.patch("admisiones.services.legales_service.Admision.objects.filter", return_value=qs)
    mocker.patch("users.services.UserPermissionService.get_coordinador_duplas", return_value=(True, [1]))
    mocker.patch("admisiones.services.legales_service.LEGALES_ADVANCED_FILTER.filter_queryset", return_value=qs)
    out = module.LegalesService.get_admisiones_legales_filtradas({"busqueda": "x"}, user=SimpleNamespace(is_superuser=False))
    assert out is qs

    # post router
    req = SimpleNamespace(POST={"btnConvenio": "1"})
    mocker.patch.object(module.LegalesService, "guardar_convenio", return_value="ok")
    assert module.LegalesService.procesar_post_legales(req, SimpleNamespace(pk=1)) == "ok"
