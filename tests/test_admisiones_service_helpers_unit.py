"""Tests for test admisiones service helpers unit."""

from datetime import datetime
from types import SimpleNamespace

from django.utils import timezone

from admisiones.services import admisiones_service as module


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
