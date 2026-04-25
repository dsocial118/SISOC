"""Tests unitarios para comedores.views.comedor."""

import contextlib
from datetime import date, datetime
from types import SimpleNamespace

from comedores.views import comedor as module


class _Req:
    def __init__(self, user=None, post=None, files=None):
        self.user = user or SimpleNamespace(is_superuser=False)
        self.POST = post or {}
        self.FILES = files or SimpleNamespace(getlist=lambda _k: [])


class _PageQS:
    def __init__(self, items):
        self.items = list(items)

    def __getitem__(self, index):
        return self.items[index]


class _AdmisionesQS:
    def __init__(self, items):
        self.items = list(items)

    def filter(self, **kwargs):
        admision_id = kwargs.get("id")
        filtered = [
            item for item in self.items if getattr(item, "id", None) == admision_id
        ]
        return _AdmisionesQS(filtered)

    def first(self):
        return self.items[0] if self.items else None

    def count(self):
        return len(self.items)


def test_comedor_list_queryset_and_context(mocker):
    view = module.ComedorListView()
    req = _Req(user=SimpleNamespace(), post={})
    view.request = req

    get_filtered = mocker.patch(
        "comedores.views.comedor.ComedorService.get_filtered_comedores",
        return_value="qs",
    )
    assert view.get_queryset() == "qs"
    get_filtered.assert_called_once_with(req, user=req.user)

    mocker.patch("django.views.generic.list.ListView.get_context_data", return_value={})
    mocker.patch(
        "comedores.views.comedor.reverse", side_effect=lambda name, **_k: f"/{name}/"
    )
    mocker.patch(
        "comedores.views.comedor.get_filters_ui_config", return_value={"ok": 1}
    )
    mocker.patch(
        "comedores.views.comedor.build_columns_context_from_fields",
        return_value={"column_active_keys": ["nombre"], "columns": ["x"]},
    )

    ctx = view.get_context_data()
    assert ctx["add_url"] == "/comedor_crear/"
    assert ctx["filters_mode"] is True
    assert ctx["active_columns"] == ["nombre"]
    assert "judicializado" in ctx["column_keys_all"]


def test_comedor_list_paginates_without_count():
    view = module.ComedorListView()
    view.request = _Req(post={"page": "1"})
    view.request.GET = {"page": "1"}
    view.page_kwarg = "page"
    items = [SimpleNamespace(pk=1), SimpleNamespace(pk=2)]

    paginator, page_obj, object_list, is_paginated = view.paginate_queryset(
        _PageQS(items), 10
    )

    assert paginator.count is None
    assert object_list == items
    assert page_obj.object_list == items
    assert is_paginated is False


def test_comedor_create_helpers_and_form_valid_paths(mocker):
    view = module.ComedorCreateView()
    user = SimpleNamespace(id=1)
    req = _Req(
        user=user,
        files=SimpleNamespace(getlist=lambda _k: ["img1", "img2"]),
    )
    view.request = req

    mocker.patch(
        "django.views.generic.edit.ModelFormMixin.get_form_kwargs", return_value={}
    )
    kwargs = view.get_form_kwargs()
    assert kwargs["user"] is user

    mocker.patch(
        "django.views.generic.edit.FormMixin.get_context_data", return_value={}
    )
    rf = mocker.patch("comedores.views.comedor.ReferenteForm", return_value="rform")
    ctx = view.get_context_data()
    assert ctx["referente_form"] == "rform"
    assert rf.called

    # form_valid success
    ref_form = SimpleNamespace(is_valid=lambda: True, save=lambda: "ref")
    mocker.patch.object(
        view, "get_context_data", return_value={"referente_form": ref_form}
    )
    mocker.patch(
        "comedores.views.comedor.transaction.atomic",
        return_value=contextlib.nullcontext(),
    )
    create_img = mocker.patch("comedores.views.comedor.ComedorService.create_imagenes")
    super_valid = mocker.patch(
        "django.views.generic.edit.ModelFormMixin.form_valid", return_value="ok"
    )

    form = SimpleNamespace(
        instance=SimpleNamespace(referente=None),
        save=lambda: SimpleNamespace(pk=9),
        add_error=mocker.Mock(),
    )
    assert view.form_valid(form) == "ok"
    assert create_img.call_count == 2
    assert super_valid.called

    # form_valid invalid referente
    bad_ref = SimpleNamespace(is_valid=lambda: False)
    mocker.patch.object(
        view, "get_context_data", return_value={"referente_form": bad_ref}
    )
    mocker.patch.object(view, "form_invalid", return_value="invalid")
    assert view.form_valid(form) == "invalid"


def test_comedor_detail_get_object_presupuestos_and_post_paths(mocker):
    view = module.ComedorDetailView()
    view.kwargs = {"pk": 7}
    view.request = SimpleNamespace(user=SimpleNamespace())

    get_obj = mocker.patch(
        "comedores.views.comedor.ComedorService.get_comedor_detail_object",
        return_value="obj",
    )
    assert view.get_object() == "obj"
    get_obj.assert_called_once_with(7, user=view.request.user)

    # get_presupuestos_data cache hit
    view.object = SimpleNamespace(id=1, relevamientos_optimized=[1])
    mocker.patch("comedores.views.comedor.cache.get", return_value=(1, 2, 3, 4, 5, 6))
    data = view.get_presupuestos_data()
    assert data["count_beneficiarios"] == 1
    assert data["monto_prestacion_mensual"] == 6

    # post descartar_expediente sin permisos
    req = _Req(
        user=SimpleNamespace(is_superuser=False),
        post={"action": "descartar_expediente"},
    )
    view.get_object = lambda: SimpleNamespace(pk=7)
    err = mocker.patch("comedores.views.comedor.messages.error")
    mocker.patch("comedores.views.comedor.redirect", return_value="redir")
    assert view.post(req) == "redir"
    assert err.called

    # post descartar_expediente con permisos y datos completos
    admision = SimpleNamespace(
        enviada_a_archivo=False,
        motivo_descarte_expediente=None,
        fecha_descarte_expediente=None,
        estado=None,
        estado_legales=None,
        save=mocker.Mock(),
    )
    req2 = _Req(
        user=SimpleNamespace(is_superuser=True),
        post={
            "action": "descartar_expediente",
            "admision_id": "11",
            "motivo_descarte": "x",
        },
    )
    view.get_object = lambda: SimpleNamespace(pk=7)
    mocker.patch("comedores.views.comedor.Admision.objects.get", return_value=admision)
    mocker.patch(
        "comedores.views.comedor.EstadoAdmision.objects.get_or_create",
        return_value=("desc", True),
    )
    success = mocker.patch("comedores.views.comedor.messages.success")
    mocker.patch("comedores.views.comedor.redirect", return_value="redir2")
    assert view.post(req2) == "redir2"
    assert success.called

    req3 = _Req(user=SimpleNamespace(is_superuser=False), post={"territorial": "1"})
    view.get_object = lambda: SimpleNamespace(pk=7)
    view.object = SimpleNamespace(pk=7)
    err_legacy = mocker.patch("comedores.views.comedor.messages.error")
    redirect_legacy = mocker.patch(
        "comedores.views.comedor.redirect", return_value="redir3"
    )
    assert view.post(req3) == "redir3"
    err_legacy.assert_called_once()
    redirect_legacy.assert_called_with("relevamientos", comedor_pk=7)


def test_comedor_detail_helpers_nomina_chart_and_safe_cell():
    metrics = module._build_nomina_metrics(
        10,
        {
            "ninos": 2,
            "adolescentes": 3,
            "adultos": 4,
            "adultos_mayores": 1,
            "adulto_mayor_avanzado": 0,
            "total_activos": 8,
        },
    )
    assert metrics["nomina_menores"] == 5
    assert metrics["nomina_pct_sin_dato"] == 20
    assert metrics["nomina_pct_adultos"] == 40

    labels, values = module._build_interacciones_chart_data(
        [
            date(2024, 1, 10),
            date(2024, 1, 12),
            None,
            date(2024, 2, 1),
        ]
    )
    assert labels == ["Ene 2024", "Feb 2024"]
    assert values == [2, 1]

    assert module._safe_cell_content(None) == "-"
    assert str(module._safe_cell_content("<b>x</b>")) == "&lt;b&gt;x&lt;/b&gt;"


def test_build_organizacion_responsables_context_filtra_y_formatea():
    class _RelatedList:
        def __init__(self, items):
            self._items = items

        def all(self):
            return self._items

    organizacion = SimpleNamespace(
        nombre="Org Centro",
        cuit=20333444556,
        tipo_entidad="Asociacion Civil",
        subtipo_entidad=None,
        email="org@example.com",
        telefono=None,
        fecha_vencimiento=datetime(2026, 5, 2, 10, 0, 0),
        firmantes=_RelatedList(
            [
                SimpleNamespace(
                    nombre="Ana Perez",
                    cuit=27111222333,
                    rol=SimpleNamespace(nombre="Presidenta"),
                ),
                SimpleNamespace(
                    nombre="Luis Gomez",
                    cuit=None,
                    rol=None,
                ),
                SimpleNamespace(
                    nombre="",
                    cuit=None,
                    rol=None,
                ),
            ]
        ),
        avales=_RelatedList(
            [
                SimpleNamespace(nombre="Carlos Aval", cuit=20999888777),
                SimpleNamespace(nombre=None, cuit=None),
            ]
        ),
    )

    context = module._build_organizacion_responsables_context(
        SimpleNamespace(organizacion=organizacion)
    )

    assert [item["label"] for item in context["responsables_organizacion_items"]] == [
        "Nombre",
        "CUIT",
        "Tipo de entidad",
        "Email",
        "Fecha de vencimiento de mandatos",
    ]
    assert [firmante["text"] for firmante in context["responsables_firmantes"]] == [
        "Presidenta: Ana Perez 27111222333",
        "Luis Gomez",
    ]
    assert context["responsables_avales"] == [
        {
            "icon": "bi bi-shield-check",
            "label": "Aval 1",
            "value": "Carlos Aval 20999888777",
        }
    ]


def test_comedor_detail_selected_admision_helpers_and_prestaciones(mocker):
    admision_1 = SimpleNamespace(id=1, convenio_numero="123")
    admision_activa = SimpleNamespace(id=2, convenio_numero=None, numero_convenio="456")
    admisiones_qs = _AdmisionesQS([admision_1, admision_activa])

    assert module._parse_selected_admision_pk("1") == 1
    assert module._parse_selected_admision_pk("x") is None

    _, selected = module._resolve_selected_admision({"admision": admisiones_qs}, 1)
    assert selected is admision_1

    _, selected_fallback = module._resolve_selected_admision(
        {"admision": admisiones_qs, "admision_activa": admision_activa}, 99
    )
    assert selected_fallback is admision_activa
    assert module._resolve_selected_convenio_numero(admision_activa) == 456

    mocker.patch.object(
        module.ComedorService,
        "get_prestaciones_aprobadas_por_tipo",
        return_value={"desayuno": 2, "almuerzo": 3},
    )
    mocker.patch.object(
        module.ComedorService,
        "calcular_monto_prestacion_mensual_por_aprobadas",
        return_value=999,
    )
    prestaciones_ctx = module._build_prestaciones_aprobadas_context(
        SimpleNamespace(pk=10)
    )
    assert prestaciones_ctx["prestaciones_aprobadas_total"] == 5
    assert prestaciones_ctx["monto_prestacion_mensual_aprobadas"] == 999

    empty_prestaciones_ctx = module._build_prestaciones_aprobadas_context(None)
    assert empty_prestaciones_ctx["prestaciones_aprobadas_total"] is None

    mocker.patch(
        "comedores.views.comedor._get_informe_tecnico_finalizado_from_admision",
        return_value=None,
    )
    selected_ctx = module._build_selected_admision_context(
        {"admision": admisiones_qs}, {"admision_id": "1"}
    )
    assert selected_ctx["selected_admision"] is admision_1
    assert selected_ctx["selected_convenio_numero"] == "123"


def test_comedor_detail_get_context_data_selected_admision_flow(mocker):
    view = module.ComedorDetailView()
    view.request = _Req(user=SimpleNamespace(is_superuser=False), post={})
    view.request.GET = {"admision_id": "1"}
    view.object = SimpleNamespace(id=7)

    admision_1 = SimpleNamespace(id=1, convenio_numero="C-1")
    admisiones_qs = _AdmisionesQS([admision_1])

    mocker.patch(
        "django.views.generic.detail.SingleObjectMixin.get_context_data",
        return_value={},
    )
    mocker.patch.object(
        view,
        "get_presupuestos_data",
        return_value={"count_beneficiarios": 10},
    )
    mocker.patch.object(
        view,
        "get_relaciones_optimizadas",
        return_value={"admision": admisiones_qs},
    )
    mocker.patch(
        "comedores.views.comedor._get_informe_tecnico_finalizado_from_admision",
        return_value=SimpleNamespace(id=90),
    )
    mocker.patch(
        "comedores.views.comedor._build_prestaciones_aprobadas_context",
        return_value={
            "prestaciones_aprobadas_total": 5,
            "monto_prestacion_mensual_aprobadas": 1000,
        },
    )
    mocker.patch(
        "comedores.views.comedor.ComedorService.get_admision_timeline_context_from_admision",
        return_value={"timeline_key": "ok"},
    )
    mocker.patch("comedores.views.comedor.IntervencionForm", return_value="iform")
    mocker.patch("comedores.views.comedor.ObservacionForm", return_value="oform")

    ctx = view.get_context_data()

    assert ctx["selected_admision"] is admision_1
    assert ctx["selected_admision_id"] == 1
    assert ctx["selected_convenio_numero"] == "C-1"
    assert ctx["prestaciones_aprobadas_total"] == 5
    assert ctx["monto_prestacion_mensual"] == 1000
    assert ctx["timeline_key"] == "ok"


def test_comedor_detail_get_relaciones_optimizadas_compone_contextos(mocker):
    view = module.ComedorDetailView()
    view.request = _Req(user=SimpleNamespace(is_superuser=False), post={})
    view.request.GET = {}

    relevamiento = SimpleNamespace(
        anexo=SimpleNamespace(
            apoyo_escolar=True,
            promocion_salud=False,
            actividades_recreativas=False,
            actividades_religiosas=False,
            actividades_jardin_maternal=False,
            alfabetizacion_terminalidad=False,
            actividades_huerta=False,
            actividades_culturales=False,
        )
    )
    clasificacion = SimpleNamespace(id=1)
    comedor_obj = SimpleNamespace(
        id=7,
        relevamientos_optimized=[relevamiento],
        observaciones_optimized=[SimpleNamespace(id=11)],
        clasificaciones_optimized=[clasificacion],
    )
    view.object = comedor_obj

    mocker.patch.object(
        module.ComedorService, "get_relevamiento_resumen", return_value=relevamiento
    )
    mocker.patch(
        "comedores.views.comedor._build_admisiones_y_nomina_context",
        return_value={
            "admisiones_qs": "admisiones",
            "timeline_context": {"admision_activa": "A"},
            "nomina_total": 10,
            "nomina_hombres": 4,
            "nomina_mujeres": 6,
            "nomina_rangos": {},
            "nomina_menores": 2,
            "nomina_espera": 1,
            "nomina_pct_sin_dato": 0,
            "nomina_pct_ninos": 10,
            "nomina_pct_adolescentes": 20,
            "nomina_pct_adultos": 30,
            "nomina_pct_adultos_mayores": 40,
            "nomina_pct_adulto_mayor_avanzado": 50,
        },
    )
    mocker.patch(
        "comedores.views.comedor._build_intervenciones_table_context",
        return_value={"intervenciones_items": [1]},
    )
    mocker.patch(
        "comedores.views.comedor._build_observaciones_table_context",
        return_value={"observaciones_items": [2]},
    )
    mocker.patch(
        "comedores.views.comedor._build_interacciones_context",
        return_value={"interacciones_labels": "[]"},
    )
    mocker.patch(
        "comedores.views.comedor._build_admisiones_table_context",
        return_value={"admisiones_items": [3]},
    )
    mocker.patch(
        "comedores.views.comedor._build_imagenes_y_programa_history_context",
        return_value={"imagenes": [], "programa_history": []},
    )
    mocker.patch(
        "comedores.views.comedor._build_validaciones_table_context",
        return_value={"validaciones_items": [4]},
    )
    mocker.patch(
        "comedores.views.comedor.AcompanamientoService.obtener_admisiones_para_selector",
        return_value=[],
    )

    ctx = view.get_relaciones_optimizadas()

    assert ctx["count_relevamientos"] == 1
    assert ctx["actividades_comunitarias_count"] == 1
    assert ctx["comedor_categoria"] is clasificacion
    assert ctx["admision"] == "admisiones"
    assert ctx["intervenciones_items"] == [1]
    assert ctx["observaciones_items"] == [2]
    assert ctx["admisiones_items"] == [3]
    assert ctx["validaciones_items"] == [4]


def test_count_actividades_comunitarias():
    anexo = SimpleNamespace(
        apoyo_escolar=True,
        promocion_salud=False,
        actividades_recreativas=True,
        actividades_religiosas=False,
        actividades_jardin_maternal=False,
        alfabetizacion_terminalidad=True,
        actividades_huerta=False,
        actividades_culturales=True,
    )
    assert module._count_actividades_comunitarias(anexo) == 4
    assert module._count_actividades_comunitarias(None) == 0


def test_build_intervenciones_table_context(mocker):
    class _FakeQS(list):
        def select_related(self, *_args):
            return self

        def order_by(self, *_args):
            return self

    class _FakePage(list):
        number = 1

        def has_other_pages(self):
            return False

    intervencion = SimpleNamespace(
        pk=10,
        id=10,
        fecha=date(2024, 2, 1),
        tipo_intervencion="Visita",
        subintervencion="Seguimiento",
        destinatario="Comedor",
        tiene_documentacion=True,
    )
    page_obj = _FakePage([intervencion])
    paginator = SimpleNamespace(
        get_page=lambda _page: page_obj,
        get_elided_page_range=lambda number=None: [1],
    )

    mocker.patch.object(
        module.Intervencion,
        "objects",
        SimpleNamespace(filter=lambda **_kwargs: _FakeQS([intervencion])),
    )
    mocker.patch("comedores.views.comedor.Paginator", return_value=paginator)
    mocker.patch(
        "comedores.views.comedor._build_intervencion_creator_map",
        return_value={
            10: SimpleNamespace(
                get_full_name=lambda: "Usuario Creador", username="ucreator"
            )
        },
    )
    mocker.patch(
        "comedores.views.comedor.reverse",
        side_effect=lambda name, args=None, **_kwargs: f"/{name}/{(args or [''])[0]}",
    )

    request = SimpleNamespace(
        GET={"intervenciones_page": "2"},
        user=SimpleNamespace(is_superuser=True),
    )
    comedor_obj = SimpleNamespace(id=77)

    ctx = module._build_intervenciones_table_context(comedor_obj, request)

    assert len(ctx["intervenciones_headers"]) == 7
    assert ctx["intervenciones_page_obj"] is page_obj
    assert ctx["intervenciones_page_range"] == [1]
    assert ctx["intervenciones_is_paginated"] is False
    row_cells = ctx["intervenciones_items"][0]["cells"]
    assert row_cells[0]["content"] == "01/02/2024"
    assert row_cells[5]["content"] == "Usuario Creador"
    assert "Ver" in str(row_cells[6]["content"])
    assert "Eliminar" in str(row_cells[6]["content"])


def test_build_observaciones_table_context(mocker):
    class _FakeQS(list):
        def order_by(self, *_args):
            return self

        def select_related(self, *_args):
            return self

    class _FakePage(list):
        number = 1

        def has_other_pages(self):
            return True

    observacion = SimpleNamespace(
        id=33,
        fecha_visita=datetime(2024, 3, 5, 14, 30),
        observador="Trabajadora",
        observacion="Observacion extensa " * 10,
    )
    page_obj = _FakePage([observacion])
    paginator = SimpleNamespace(
        get_page=lambda _page: page_obj,
        get_elided_page_range=lambda number=None: [1, 2, 3],
    )

    mocker.patch.object(
        module.Observacion,
        "objects",
        SimpleNamespace(filter=lambda **_kwargs: _FakeQS([observacion])),
    )
    mocker.patch("comedores.views.comedor.Paginator", return_value=paginator)
    mocker.patch("comedores.views.comedor.timezone.is_naive", return_value=True)
    mocker.patch(
        "comedores.views.comedor.timezone.make_aware",
        side_effect=lambda value: value,
    )
    mocker.patch(
        "comedores.views.comedor.timezone.localtime",
        side_effect=lambda value: value,
    )
    mocker.patch(
        "comedores.views.comedor.reverse",
        side_effect=lambda name, kwargs=None, **_x: f"/{name}/{kwargs['pk']}",
    )

    request = SimpleNamespace(GET={"observaciones_page": "3"})
    comedor_obj = SimpleNamespace(id=9)

    ctx = module._build_observaciones_table_context(comedor_obj, request)

    assert len(ctx["observaciones_headers"]) == 4
    assert ctx["observaciones_page_obj"] is page_obj
    assert ctx["observaciones_is_paginated"] is True
    assert ctx["observaciones_page_range"] == [1, 2, 3]
    row_cells = ctx["observaciones_items"][0]["cells"]
    assert row_cells[0]["content"] == "05/03/2024 14:30"
    assert row_cells[1]["content"] == "Trabajadora"
    assert "Ver" in str(row_cells[3]["content"])


def test_build_validaciones_table_context(mocker):
    class _FakeQS(list):
        def select_related(self, *_args):
            return self

        def order_by(self, *_args):
            return self

    class _FakePage(list):
        number = 2

        def has_other_pages(self):
            return True

    validacion = SimpleNamespace(
        fecha_validacion=datetime(2024, 4, 10, 9, 15),
        usuario=SimpleNamespace(get_full_name=lambda: "", username="tester"),
        estado_validacion="No Validado",
        get_opciones_display=lambda: "Datos inconsistentes",
        comentario="<script>x</script>",
    )
    page_obj = _FakePage([validacion])
    paginator = SimpleNamespace(get_page=lambda _page: page_obj)
    historial_manager = SimpleNamespace(
        select_related=lambda *_args: _FakeQS([validacion]),
    )

    mocker.patch("comedores.views.comedor.Paginator", return_value=paginator)
    mocker.patch("comedores.views.comedor.timezone.is_naive", return_value=True)
    mocker.patch(
        "comedores.views.comedor.timezone.make_aware",
        side_effect=lambda value: value,
    )
    mocker.patch(
        "comedores.views.comedor.timezone.localtime",
        side_effect=lambda value: value,
    )

    comedor_obj = SimpleNamespace(historial_validaciones=historial_manager)
    request = SimpleNamespace(GET={"page": "2"})

    ctx = module._build_validaciones_table_context(comedor_obj, request)

    assert ctx["historial_validaciones"] == [validacion]
    assert ctx["is_paginated"] is True
    assert ctx["page_obj"] is page_obj
    row_cells = ctx["validaciones_items"][0]["cells"]
    assert row_cells[0]["content"] == "10/04/2024 09:15"
    assert row_cells[1]["content"] == "tester"
    assert "No Validado" in str(row_cells[2]["content"])
    assert row_cells[3]["content"] == "Datos inconsistentes"
    assert row_cells[4]["content"] == "&lt;script&gt;x&lt;/script&gt;"


def test_build_admisiones_table_context(mocker):
    class _FakePage(list):
        number = 1

        def has_other_pages(self):
            return False

    admision = SimpleNamespace(
        id=15,
        creado=datetime(2024, 5, 1, 8, 0),
        num_expediente="EXP-123",
        numero_convenio="CV-1",
        tipo="x",
        get_tipo_display=lambda: "Nuevo",
        estado_mostrar="En curso",
        fecha_estado_mostrar=date(2024, 5, 2),
        convenio_numero=7,
        activa=True,
        enviada_a_archivo=False,
        enviado_acompaniamiento=False,
    )
    page_obj = _FakePage([admision])
    paginator = SimpleNamespace(
        get_page=lambda _page: page_obj,
        get_elided_page_range=lambda number=None: [1],
    )

    mocker.patch("comedores.views.comedor.Paginator", return_value=paginator)
    mocker.patch(
        "comedores.views.comedor.reverse",
        side_effect=lambda name, args=None, **_kwargs: (
            f"/{name}/" + "/".join(str(arg) for arg in (args or []))
        ),
    )

    request = SimpleNamespace(
        GET={"admisiones_page": "1"},
        user=SimpleNamespace(is_superuser=True),
    )
    ctx = module._build_admisiones_table_context(
        comedor_id=77,
        admisiones_qs=[admision],
        request=request,
    )

    assert len(ctx["admisiones_headers"]) == 9
    assert ctx["admisiones_page_obj"] is page_obj
    assert ctx["admisiones_is_paginated"] is False
    row = ctx["admisiones_items"][0]
    row_cells = row["cells"]
    assert row["admision_id"] == 15
    assert row_cells[0]["content"] == "01/05/2024"
    assert row_cells[3]["content"] == "Nuevo"
    assert "Descartar Expediente" in str(row_cells[8]["content"])


def test_build_interacciones_and_media_programa_context(mocker):
    class _FakeIntervencionDateQS(list):
        def values_list(self, *_args, **_kwargs):
            return self

        def order_by(self, *_args, **_kwargs):
            return self

    mocker.patch.object(
        module.Intervencion,
        "objects",
        SimpleNamespace(
            filter=lambda **_kwargs: _FakeIntervencionDateQS(
                [date(2024, 1, 1), date(2024, 1, 10), date(2024, 2, 1)]
            )
        ),
    )

    interacciones_ctx = module._build_interacciones_context(SimpleNamespace(id=1))
    assert interacciones_ctx["interacciones_labels"] == '["Ene 2024", "Feb 2024"]'
    assert interacciones_ctx["interacciones_values"] == "[2, 1]"

    comedor_prefetched = SimpleNamespace(
        imagenes_optimized=[
            SimpleNamespace(imagen="a.jpg"),
            SimpleNamespace(imagen="b.jpg"),
        ],
        programa_changes_optimized=["c1", "c2"],
    )
    media_ctx_prefetched = module._build_imagenes_y_programa_history_context(
        comedor_prefetched
    )
    assert media_ctx_prefetched["imagenes"] == [
        {"imagen": "a.jpg"},
        {"imagen": "b.jpg"},
    ]
    assert media_ctx_prefetched["programa_history"] == ["c1", "c2"]

    class _FakeProgramChanges(list):
        def select_related(self, *_args):
            return self

        def order_by(self, *_args):
            return self

    comedor_fallback = SimpleNamespace(
        imagenes=SimpleNamespace(values=lambda *_args: [{"imagen": "c.jpg"}]),
        programa_changes=_FakeProgramChanges(["x", "y"]),
    )
    media_ctx_fallback = module._build_imagenes_y_programa_history_context(
        comedor_fallback
    )
    assert media_ctx_fallback["imagenes"] == [{"imagen": "c.jpg"}]
    assert media_ctx_fallback["programa_history"] == ["x", "y"]


def test_build_admisiones_y_nomina_context(mocker):
    class _FakeAdmisionQS(list):
        def select_related(self, *_args):
            return self

        def order_by(self, *_args):
            return self

    admisiones_qs = _FakeAdmisionQS([SimpleNamespace(id=1), SimpleNamespace(id=2)])
    mocker.patch.object(
        module.Admision,
        "objects",
        SimpleNamespace(filter=lambda **_kwargs: admisiones_qs),
    )
    timeline_mock = mocker.patch(
        "comedores.views.comedor.ComedorService.get_admision_timeline_context",
        return_value={
            "timeline_steps": ["x"],
            "admision_activa": SimpleNamespace(id=2),
        },
    )
    nomina_mock = mocker.patch(
        "comedores.views.comedor.ComedorService.get_nomina_detail",
        return_value=(
            None,
            10,
            15,
            None,
            3,
            30,
            {
                "ninos": 5,
                "adolescentes": 4,
                "adultos": 12,
                "adultos_mayores": 6,
                "adulto_mayor_avanzado": 1,
                "total_activos": 28,
            },
        ),
    )

    comedor_obj = SimpleNamespace(pk=99)
    ctx = module._build_admisiones_y_nomina_context(comedor_obj)

    assert ctx["admisiones_qs"] is admisiones_qs
    assert ctx["timeline_context"]["admision_activa"].id == 2
    assert ctx["nomina_total"] == 30
    assert ctx["nomina_hombres"] == 10
    assert ctx["nomina_mujeres"] == 15
    assert ctx["nomina_espera"] == 3
    assert ctx["nomina_menores"] == 9
    assert ctx["nomina_pct_adultos"] == 40
    timeline_mock.assert_called_once_with(admisiones_qs)
    nomina_mock.assert_called_once_with(2, page=1, per_page=1)
