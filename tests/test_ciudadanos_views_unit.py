"""Tests unitarios para ciudadanos.views."""

from contextlib import nullcontext
from types import SimpleNamespace

from ciudadanos import views as module


class _ExpedientesList(list):
    def first(self):
        return self[0] if self else None


class _Session(dict):
    modified = False


class _OrderableResult(list):
    def order_by(self, *args):
        return self


def test_ciudadanos_list_view_get_queryset_filtra(mocker):
    qs = mocker.Mock()
    qs.filter.return_value = qs
    order_by_mock = mocker.patch(
        "ciudadanos.views.Ciudadano.objects.order_by", return_value=qs
    )

    form = mocker.Mock()
    form.is_valid.return_value = True
    form.cleaned_data = {"q": " Juan ", "provincia": "PBA", "tipo_registro": ""}
    mocker.patch("ciudadanos.views.CiudadanoFiltroForm", return_value=form)

    view = module.CiudadanosListView()
    view.request = SimpleNamespace(GET={"q": "Juan"})

    result = view.get_queryset()
    assert result == qs
    order_by_mock.assert_called_once_with("pk")
    assert qs.filter.called


def test_apply_ciudadanos_filters_usa_documento_prefix_para_q_numerico(mocker):
    qs = mocker.Mock()
    qs.filter.return_value = qs
    prefix_filter = object()
    prefix_mock = mocker.patch(
        "ciudadanos.views.Ciudadano.documento_prefix_filter",
        return_value=prefix_filter,
    )

    result = module.apply_ciudadanos_filters(qs, {"q": "12345678", "provincia": None})

    assert result == qs
    prefix_mock.assert_called_once_with("12345678")
    qs.filter.assert_called_once_with(prefix_filter)


def test_apply_ciudadanos_filters_textual_no_toca_documento(mocker):
    qs = mocker.Mock()
    qs.filter.return_value = qs
    prefix_mock = mocker.patch("ciudadanos.views.Ciudadano.documento_prefix_filter")

    result = module.apply_ciudadanos_filters(
        qs,
        {
            "q": "CIU-11",
            "provincia": None,
            "tipo_registro": module.Ciudadano.TIPO_REGISTRO_SIN_DNI,
        },
    )

    assert result == qs
    prefix_mock.assert_not_called()
    assert qs.filter.call_count == 2
    assert qs.filter.call_args_list[-1].kwargs == {
        "tipo_registro_identidad": module.Ciudadano.TIPO_REGISTRO_SIN_DNI
    }


def test_hydrate_ciudadanos_page_preserva_orden(mocker):
    ciudadano_2 = SimpleNamespace(pk=2)
    ciudadano_5 = SimpleNamespace(pk=5)
    filtered_qs = [ciudadano_5, ciudadano_2]
    base_qs = SimpleNamespace(filter=lambda **_kwargs: filtered_qs)
    mocker.patch(
        "ciudadanos.views.build_ciudadanos_list_row_queryset",
        return_value=base_qs,
    )

    result = module.hydrate_ciudadanos_page([2, 5])

    assert result == [ciudadano_2, ciudadano_5]


def test_no_count_paginator_navega_sin_count_exacto():
    paginator = module.NoCountPaginator(list(range(7)), 3)

    first_page = paginator.get_page("1")
    assert first_page.object_list == [0, 1, 2]
    assert first_page.has_previous() is False
    assert first_page.has_next() is True
    assert first_page.next_page_number() == 2
    assert first_page.paginator.count is None

    last_page = paginator.get_page(3)
    assert last_page.object_list == [6]
    assert last_page.has_previous() is True
    assert last_page.has_next() is False
    assert last_page.previous_page_number() == 2


def test_ciudadanos_list_view_build_page_range_sin_total():
    paginator = module.NoCountPaginator(list(range(80)), 25)
    page_obj = paginator.get_page(3)

    assert module.build_no_count_page_range(page_obj) == [1, 2, 3, 4, "..."]


def test_ciudadanos_detail_helpers_contexts(mocker):
    ciudadano = SimpleNamespace(pk=7)

    mocker.patch(
        "celiaquia.models.ExpedienteCiudadano.objects.filter",
        side_effect=Exception("boom"),
    )
    log_exc = mocker.patch("ciudadanos.views.logger.exception")
    out_err = module.CiudadanosDetailView().get_celiaquia_context(ciudadano)
    assert out_err == {"expedientes_celiaquia": []}
    assert log_exc.called

    exped = SimpleNamespace(id=1)
    qs = _ExpedientesList([exped])
    mocker.patch(
        "celiaquia.models.ExpedienteCiudadano.objects.filter",
        return_value=SimpleNamespace(
            select_related=lambda *a, **k: SimpleNamespace(order_by=lambda *x, **y: qs)
        ),
    )
    out_ok = module.CiudadanosDetailView().get_celiaquia_context(ciudadano)
    assert out_ok["expediente_actual"] is exped


def test_ciudadanos_create_busqueda_paths(mocker):
    view = module.CiudadanosCreateView()
    request = SimpleNamespace(GET={}, session=_Session(), headers={})

    super_get = mocker.patch(
        "django.views.generic.edit.BaseCreateView.get",
        return_value="super-get",
    )
    msg_warn = mocker.patch("ciudadanos.views.messages.warning")
    msg_info = mocker.patch("ciudadanos.views.messages.info")
    msg_success = mocker.patch("ciudadanos.views.messages.success")
    redir = mocker.patch(
        "ciudadanos.views.redirect", side_effect=lambda *a, **k: (a, k)
    )

    invalid = view._handle_ciudadano_busqueda(request, "abc", None)
    assert invalid == "super-get"
    assert msg_warn.called

    existing = SimpleNamespace(
        pk=5,
        tipo_registro_identidad=module.Ciudadano.TIPO_REGISTRO_ESTANDAR,
    )
    mocker.patch(
        "ciudadanos.views.Ciudadano.objects.filter",
        return_value=_OrderableResult([existing]),
    )
    exists_resp = view._handle_ciudadano_busqueda(request, "12345678", None)
    assert exists_resp[0][0] == "ciudadanos_editar"
    assert msg_info.called

    mocker.patch(
        "ciudadanos.views.Ciudadano.objects.filter",
        return_value=_OrderableResult([]),
    )
    mocker.patch(
        "ciudadanos.views.ComedorService.obtener_datos_ciudadano_desde_renaper",
        return_value={"success": False, "message": "no"},
    )
    not_found = view._handle_ciudadano_busqueda(request, "12345678", None)
    assert not_found == "super-get"

    mocker.patch(
        "ciudadanos.views.ComedorService.obtener_datos_ciudadano_desde_renaper",
        return_value={
            "success": True,
            "data": {"documento": 123, "fecha_nacimiento": "2020-01-01"},
        },
    )
    ok = view._handle_ciudadano_busqueda(request, "12345678", None)
    assert ok == "super-get"
    assert request.session.get("ciudadano_prefill")
    assert msg_success.called
    assert super_get.called
    assert redir.called


def test_ciudadanos_create_get_form_and_safe_int(mocker):
    view = module.CiudadanosCreateView()
    view._prefill_ciudadano = {"provincia": "1", "municipio": "2", "localidad": "3"}

    form = SimpleNamespace(
        fields={
            "provincia": SimpleNamespace(initial=None, queryset=None),
            "municipio": SimpleNamespace(initial=None, queryset=None),
            "localidad": SimpleNamespace(initial=None, queryset=None),
        }
    )
    mocker.patch("django.views.generic.edit.ModelFormMixin.get_form", return_value=form)

    localidad_obj = SimpleNamespace(
        municipio_id=2, municipio=SimpleNamespace(provincia_id=1)
    )
    mocker.patch(
        "ciudadanos.views.Localidad.objects.select_related",
        return_value=SimpleNamespace(
            filter=lambda **k: SimpleNamespace(first=lambda: localidad_obj)
        ),
    )
    mocker.patch(
        "ciudadanos.views.Municipio.objects.filter",
        return_value=SimpleNamespace(order_by=lambda *_a, **_k: ["mun"]),
    )
    mocker.patch(
        "ciudadanos.views.Localidad.objects.filter",
        return_value=SimpleNamespace(order_by=lambda *_a, **_k: ["loc"]),
    )

    built = view.get_form()
    assert built is form
    assert form.fields["provincia"].initial == 1
    assert form.fields["municipio"].initial == 2
    assert form.fields["localidad"].initial == 3

    assert module.CiudadanosCreateView._safe_int("7") == 7
    assert module.CiudadanosCreateView._safe_int("x") is None


def test_grupofamiliar_delete_get_success_url_uses_safe_redirect(mocker):
    view = module.GrupoFamiliarDeleteView()
    view.request = SimpleNamespace(POST={"next": "/volver"}, GET={})
    view.object = SimpleNamespace(
        ciudadano_1=SimpleNamespace(get_absolute_url=lambda: "/base")
    )

    mocker.patch(
        "ciudadanos.views.messages.success",
    )
    mocker.patch(
        "ciudadanos.views.safe_redirect",
        return_value=SimpleNamespace(url="/destino"),
    )

    assert view.get_success_url() == "/destino"


def test_ciudadanos_detail_cdf_and_comedor_contexts(mocker):
    ciudadano = SimpleNamespace(pk=9)

    # CDF import error
    orig_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "centrodefamilia.models":
            raise ImportError("no cdf")
        return orig_import(name, *args, **kwargs)

    mocker.patch("builtins.__import__", side_effect=fake_import)
    cdf_ctx = module.CiudadanosDetailView().get_cdf_context(ciudadano)
    assert cdf_ctx == {"participaciones_cdf": [], "costo_total_cdf": 0}

    mocker.patch("builtins.__import__", side_effect=orig_import)
    part_qs = _ExpedientesList([SimpleNamespace(id=1)])
    mocker.patch(
        "centrodefamilia.models.ParticipanteActividad.objects.filter",
        side_effect=[
            SimpleNamespace(
                select_related=lambda *a, **k: SimpleNamespace(
                    order_by=lambda *x, **y: part_qs
                )
            ),
            SimpleNamespace(aggregate=lambda **_k: {"total": 1200}),
        ],
    )
    cdf_ok = module.CiudadanosDetailView().get_cdf_context(ciudadano)
    assert cdf_ok["costo_total_cdf"] == 1200

    # Comedor import error
    def fake_import2(name, *args, **kwargs):
        if name == "comedores.models":
            raise ImportError("no comedor")
        return orig_import(name, *args, **kwargs)

    mocker.patch("builtins.__import__", side_effect=fake_import2)
    comedor_ctx = module.CiudadanosDetailView().get_comedor_context(ciudadano)
    assert comedor_ctx == {"nominas_comedor": [], "colaboraciones_comedor": []}

    mocker.patch("builtins.__import__", side_effect=orig_import)
    nom_qs = _ExpedientesList([SimpleNamespace(id=7)])
    colab_qs = _ExpedientesList([SimpleNamespace(id=9)])

    def _select_related_nomina(*args, **kwargs):
        assert args == (
            "admision__comedor__provincia",
            "admision__comedor__municipio",
            "admision__comedor__tipocomedor",
        )
        return SimpleNamespace(order_by=lambda *x, **y: nom_qs)

    def _select_related_colaborador(*args, **kwargs):
        assert args == (
            "comedor__provincia",
            "comedor__municipio",
            "comedor__tipocomedor",
        )
        return SimpleNamespace(
            prefetch_related=lambda *x, **y: SimpleNamespace(
                order_by=lambda *a, **b: colab_qs
            )
        )

    mocker.patch(
        "comedores.models.Nomina.objects.filter",
        return_value=SimpleNamespace(select_related=_select_related_nomina),
    )
    mocker.patch(
        "comedores.models.ColaboradorEspacio.objects.filter",
        return_value=SimpleNamespace(select_related=_select_related_colaborador),
    )
    comedor_ok = module.CiudadanosDetailView().get_comedor_context(ciudadano)
    assert comedor_ok["nomina_actual"].id == 7
    assert comedor_ok["colaboraciones_comedor"][0].id == 9


def test_ciudadanos_detail_vat_context_resume_por_programa(mocker):
    ciudadano = SimpleNamespace(pk=12)

    programa_a = SimpleNamespace(id=1, __str__=lambda self: "Programa A")
    programa_b = SimpleNamespace(id=2, __str__=lambda self: "Programa B")

    voucher_activo = SimpleNamespace(
        pk=11,
        programa=programa_a,
        estado="activo",
        cantidad_inicial=10,
        cantidad_disponible=4,
        get_estado_display=lambda: "Activo",
    )
    voucher_agotado = SimpleNamespace(
        pk=12,
        programa=programa_a,
        estado="agotado",
        cantidad_inicial=5,
        cantidad_disponible=0,
        get_estado_display=lambda: "Agotado",
    )
    voucher_programa_b = SimpleNamespace(
        pk=13,
        programa=programa_b,
        estado="cancelado",
        cantidad_inicial=2,
        cantidad_disponible=0,
        get_estado_display=lambda: "Cancelado",
    )

    inscripcion_a1 = SimpleNamespace(id=21, programa=programa_a)
    inscripcion_a2 = SimpleNamespace(id=22, programa=programa_a)
    inscripcion_b1 = SimpleNamespace(id=23, programa=programa_b)

    inscripcion_oferta_a = SimpleNamespace(
        pk=31,
        oferta=SimpleNamespace(oferta=SimpleNamespace(programa=programa_a)),
    )

    asistencias = [
        SimpleNamespace(inscripcion_id=21, presente=True),
        SimpleNamespace(inscripcion_id=21, presente=False),
        SimpleNamespace(inscripcion_id=22, presente=True),
    ]

    class _QueryChain:
        def __init__(self, result):
            self.result = result

        def select_related(self, *args, **kwargs):
            return self

        def prefetch_related(self, *args, **kwargs):
            return self

        def order_by(self, *args, **kwargs):
            return self.result

    mocker.patch(
        "VAT.models.Inscripcion.objects.filter",
        return_value=_QueryChain(
            [
                inscripcion_a1,
                inscripcion_a2,
                inscripcion_b1,
            ]
        ),
    )
    mocker.patch(
        "VAT.models.Voucher.objects.filter",
        return_value=_QueryChain(
            [
                voucher_activo,
                voucher_agotado,
                voucher_programa_b,
            ]
        ),
    )
    mocker.patch(
        "VAT.models.InscripcionOferta.objects.filter",
        return_value=_QueryChain([inscripcion_oferta_a]),
    )
    mocker.patch(
        "VAT.models.AsistenciaSesion.objects.filter",
        return_value=_QueryChain(asistencias),
    )

    context = module.CiudadanosDetailView().get_vat_context(ciudadano)

    assert context["vat_creditos_totales"] == 17
    assert context["vat_creditos_disponibles"] == 4
    assert context["vat_voucher_activo"] is voucher_activo
    assert len(context["vat_programas"]) == 2

    programa_a_ctx = next(
        item for item in context["vat_programas"] if item["programa"] is programa_a
    )
    assert programa_a_ctx["creditos_totales"] == 15
    assert programa_a_ctx["creditos_actuales"] == 4
    assert programa_a_ctx["cursos_asignados"] == 3
    assert programa_a_ctx["asistencias_presentes"] == 2
    assert programa_a_ctx["asistencias_registradas"] == 3
    assert programa_a_ctx["voucher_activo"] is voucher_activo
    assert inscripcion_a1.asistencias_presentes == 1
    assert inscripcion_a1.asistencias_registradas == 2
    assert inscripcion_a1.asistencia_porcentaje == 50
    assert inscripcion_a2.asistencia_porcentaje == 100


def test_ciudadanos_create_and_update_form_valid_and_context(mocker):
    create_view = module.CiudadanosCreateView()
    create_view.request = SimpleNamespace(GET={"sexo": "Z"}, user=SimpleNamespace(id=1))
    mocker.patch(
        "django.views.generic.edit.FormMixin.get_context_data", return_value={}
    )
    ctx = create_view.get_context_data()
    assert ctx["sexo_busqueda"] == "M"

    # get_initial consumes prefill from session
    create_view.request = SimpleNamespace(
        session={"ciudadano_prefill": {"nombre": "Ana"}}
    )
    mocker.patch("django.views.generic.edit.FormMixin.get_initial", return_value={})
    initial = create_view.get_initial()
    assert initial["nombre"] == "Ana"

    ciudadano = SimpleNamespace(
        pk=10,
        tipo_registro_identidad=module.Ciudadano.TIPO_REGISTRO_ESTANDAR,
        tipo_documento=module.Ciudadano.DOCUMENTO_DNI,
        documento=12345678,
        identificador_interno=None,
        documento_unico_key=None,
        requiere_revision_manual=None,
        creado_por=None,
        modificado_por=None,
        save=mocker.Mock(),
        get_absolute_url=lambda: "/ciudadano/1/",
    )
    form = SimpleNamespace(save=lambda commit=False: ciudadano, save_m2m=mocker.Mock())
    create_view.request = SimpleNamespace(user=SimpleNamespace(id=2))
    mocker.patch("ciudadanos.views.transaction.atomic", return_value=nullcontext())
    mocker.patch("ciudadanos.views.messages.success")
    mocker.patch("ciudadanos.views.redirect", return_value="redir")
    assert create_view.form_valid(form) == "redir"
    assert ciudadano.creado_por.id == 2
    documento_esperado = "{}_{}".format(module.Ciudadano.DOCUMENTO_DNI, "12345678")
    assert ciudadano.documento_unico_key == documento_esperado
    assert ciudadano.identificador_interno == "CIU-10"
    assert ciudadano.requiere_revision_manual is False

    update_view = module.CiudadanosUpdateView()
    update_view.request = SimpleNamespace(user=SimpleNamespace(id=3))
    documento_previo = "{}_{}".format(module.Ciudadano.DOCUMENTO_DNI, "87654321")
    ciudadano2 = SimpleNamespace(
        pk=11,
        tipo_registro_identidad=module.Ciudadano.TIPO_REGISTRO_SIN_DNI,
        tipo_documento=module.Ciudadano.DOCUMENTO_DNI,
        documento=87654321,
        motivo_sin_dni=module.Ciudadano.MOTIVO_SIN_DNI_OTRO,
        motivo_sin_dni_descripcion="Sin datos",
        motivo_no_validacion_renaper=module.Ciudadano.MOTIVO_NO_VALIDADO_OTRO,
        motivo_no_validacion_descripcion="Debe limpiarse",
        identificador_interno="CIU-11",
        documento_unico_key=documento_previo,
        requiere_revision_manual=False,
        modificado_por=None,
        save=mocker.Mock(),
        get_absolute_url=lambda: "/c/2/",
    )
    form2 = SimpleNamespace(
        save=lambda commit=False: ciudadano2, save_m2m=mocker.Mock()
    )
    mocker.patch("ciudadanos.views.messages.success")
    mocker.patch("ciudadanos.views.redirect", return_value="redir2")
    assert update_view.form_valid(form2) == "redir2"
    assert ciudadano2.modificado_por.id == 3
    assert ciudadano2.documento is None
    assert ciudadano2.documento_unico_key is None
    assert ciudadano2.requiere_revision_manual is True
    assert ciudadano2.motivo_no_validacion_renaper is None
