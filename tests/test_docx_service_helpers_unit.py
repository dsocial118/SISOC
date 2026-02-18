"""Tests unitarios para helpers de admisiones.services.docx_service."""

from datetime import datetime
from types import SimpleNamespace

from admisiones.services import docx_service as module


class _Custom:
    def __init__(self):
        self.name = "obj"

    def hello(self):
        return "ok"


def test_docx_placeholder_behaviour():
    ph = module._DocxPlaceholder("-")
    assert bool(ph) is False
    assert len(ph) == 0
    assert ph.anything is ph
    assert ph() is ph


def test_wrap_value_for_docx_with_nested_and_proxy():
    wrapped_none = module._wrap_value_for_docx(None)
    assert isinstance(wrapped_none, module._DocxPlaceholder)

    wrapped = module._wrap_value_for_docx(
        {
            "a": [None, 1, (2, None)],
            "b": {"k": None},
            "c": {1, None},
        }
    )
    assert isinstance(wrapped["a"][0], module._DocxPlaceholder)
    assert isinstance(wrapped["a"][2][1], module._DocxPlaceholder)
    assert isinstance(wrapped["b"]["k"], module._DocxPlaceholder)

    proxy = module._wrap_value_for_docx(_Custom())
    assert isinstance(proxy, module._DocxSafeProxy)
    assert str(proxy.name) == "obj"
    assert str(proxy.hello()) == "ok"


def test_docx_safe_proxy_getitem_iter_len_and_bool():
    proxy_dict = module._DocxSafeProxy({"x": "y"}, "-")
    assert proxy_dict["x"] == "y"
    assert isinstance(proxy_dict["missing"], module._DocxPlaceholder)

    proxy_list = module._DocxSafeProxy([1, None], "-")
    values = list(proxy_list)
    assert values[0] == 1
    assert isinstance(values[1], module._DocxPlaceholder)
    assert len(proxy_list) == 2
    assert bool(proxy_list) is True

    proxy_scalar = module._DocxSafeProxy(5, "-")
    assert len(proxy_scalar) == 0


def test_document_template_sanear_contexto_variants():
    context = {
        "html_content": "<b>hola</b>",
        "nombre": "A & B",
        "none_val": None,
        "lista": [1, "<x>"],
        "dict": {"k": "v"},
    }

    out = module.DocumentTemplateService._sanear_contexto(
        context,
        campos_sin_escape=["html_content"],
        reemplazar_none=True,
    )
    assert out["html_content"] == "<b>hola</b>"
    assert out["nombre"] == "A &amp; B"
    assert out["none_val"] == ""
    assert out["lista"] == [1, "<x>"]

    out_no_replace = module.DocumentTemplateService._sanear_contexto(
        {"none_val": None}, reemplazar_none=False
    )
    assert out_no_replace["none_val"] is None


def test_reparar_docx_para_office_success_and_fallback(mocker):
    buffer = SimpleNamespace(seek=lambda *_: None)

    good_doc = SimpleNamespace(save=lambda new_buf: None)
    mocker.patch("admisiones.services.docx_service.Document", return_value=good_doc)
    ok = module.DocumentTemplateService._reparar_docx_para_office(buffer)
    assert hasattr(ok, "seek")

    mocker.patch(
        "admisiones.services.docx_service.Document", side_effect=Exception("bad")
    )
    fallback = module.DocumentTemplateService._reparar_docx_para_office(buffer)
    assert fallback is buffer


def test_text_formatter_variants():
    no_solicitan = module.TextFormatterService.formatear_texto_comida_docx(
        "<p>No se solicitan prestaciones</p>"
    )
    assert "No se solicitan" in no_solicitan

    formatted = module.TextFormatterService.formatear_texto_comida_docx(
        "Por la cantidad de 2 desayuno prestaciones, durante 1 veces por semana"
    )
    assert "2 (dos)" in formatted
    assert "1 (una) vez" in formatted

    fallback = module.TextFormatterService.formatear_texto_comida_docx(
        "<p>Texto libre</p>"
    )
    assert fallback == "Texto libre"


def test_preparar_contexto_informe_tecnico(mocker):
    informe = SimpleNamespace(
        tipo="X",
        expediente_nro="123",
        nombre_organizacion="Org",
        domicilio_organizacion="Dir",
        localidad_organizacion="Loc",
        partido_organizacion="Par",
        provincia_organizacion="Prov",
        admision=SimpleNamespace(creado=datetime(2024, 1, 1, 10, 0, 0)),
        tipo_espacio="Comedor",
        nombre_espacio="Espacio",
        domicilio_espacio="Dir2",
        barrio_espacio="Barrio",
        responsable_tarjeta_nombre="Resp",
        responsable_tarjeta_dni="123",
        responsable_tarjeta_domicilio="Dom",
        conclusiones="Ok",
        solicitudes_desayuno_lunes=1,
        solicitudes_almuerzo_lunes=1,
        solicitudes_merienda_lunes=1,
        solicitudes_cena_lunes=1,
        solicitudes_desayuno_martes=1,
        solicitudes_almuerzo_martes=1,
        solicitudes_merienda_martes=1,
        solicitudes_cena_martes=1,
        solicitudes_desayuno_miercoles=1,
        solicitudes_almuerzo_miercoles=1,
        solicitudes_merienda_miercoles=1,
        solicitudes_cena_miercoles=1,
        solicitudes_desayuno_jueves=1,
        solicitudes_almuerzo_jueves=1,
        solicitudes_merienda_jueves=1,
        solicitudes_cena_jueves=1,
        solicitudes_desayuno_viernes=1,
        solicitudes_almuerzo_viernes=1,
        solicitudes_merienda_viernes=1,
        solicitudes_cena_viernes=1,
        solicitudes_desayuno_sabado=1,
        solicitudes_almuerzo_sabado=1,
        solicitudes_merienda_sabado=1,
        solicitudes_cena_sabado=1,
        solicitudes_desayuno_domingo=1,
        solicitudes_almuerzo_domingo=1,
        solicitudes_merienda_domingo=1,
        solicitudes_cena_domingo=1,
    )

    mocker.patch(
        "admisiones.utils.generar_texto_comidas",
        return_value={
            "desayuno": "Por la cantidad de 2 desayuno prestaciones, durante 1 veces por semana"
        },
    )

    ctx = module.AdmisionesContextService.preparar_contexto_informe_tecnico(informe)
    assert ctx["total_desayunos"] == 7
    assert "(dos)" in ctx["texto_comidas"]["desayuno"]


def test_preparar_contextos_admision_convenio_disposicion(mocker):
    admision = SimpleNamespace(
        comedor="Comedor X",
        creado=datetime(2024, 2, 3, 4, 5, 0),
        historial=SimpleNamespace(
            all=lambda: SimpleNamespace(order_by=lambda *_: ["h1", "h2"])
        ),
    )

    archivo = SimpleNamespace(
        documentacion=SimpleNamespace(nombre="Doc A"),
        nombre_personalizado="Alt",
        estado="ok",
        observaciones="obs",
    )
    archivo2 = SimpleNamespace(
        documentacion=None,
        nombre_personalizado="Alt2",
        estado="pend",
        observaciones="obs2",
    )

    mocker.patch(
        "admisiones.services.docx_service.ArchivoAdmision.objects.filter",
        return_value=[archivo, archivo2],
    )
    mocker.patch(
        "admisiones.services.docx_service.InformeTecnico.objects.filter",
        return_value=SimpleNamespace(first=lambda: "inf"),
    )
    mocker.patch(
        "admisiones.services.docx_service.FormularioProyectoDeConvenio.objects.filter",
        return_value=SimpleNamespace(first=lambda: "conv"),
    )
    mocker.patch(
        "admisiones.services.docx_service.FormularioProyectoDisposicion.objects.filter",
        return_value=SimpleNamespace(first=lambda: "disp"),
    )

    ctx_adm = module.TextFormatterService.preparar_contexto_admision(admision)
    assert len(ctx_adm["documentos"]) == 2
    assert ctx_adm["documentos"][1]["nombre"] == "Alt2"

    ctx_conv = module.TextFormatterService.preparar_contexto_proyecto_convenio(admision)
    assert ctx_conv["formulario"] == "conv"

    ctx_disp = module.TextFormatterService.preparar_contexto_proyecto_disposicion(
        admision
    )
    assert ctx_disp["formulario"] == "disp"
    assert ctx_disp["proyecto_convenio"] == "conv"
