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
