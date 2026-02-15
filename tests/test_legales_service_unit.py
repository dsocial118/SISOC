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
        admisiones_proyecto_convenio=SimpleNamespace(first=lambda: None),
        admisiones_proyecto_disposicion=SimpleNamespace(first=lambda: None),
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
