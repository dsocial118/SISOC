"""Tests unitarios para ciudadanos.views."""

from types import SimpleNamespace

from ciudadanos import views as module


class _ExpedientesList(list):
    def first(self):
        return self[0] if self else None


class _Session(dict):
    modified = False


def test_ciudadanos_list_view_get_queryset_filtra(mocker):
    qs = mocker.Mock()
    qs.filter.return_value = qs
    qs.order_by.return_value = "ordered"
    mocker.patch("ciudadanos.views.Ciudadano.objects.select_related", return_value=qs)

    form = mocker.Mock()
    form.is_valid.return_value = True
    form.cleaned_data = {"q": " Juan ", "provincia": "PBA"}
    mocker.patch("ciudadanos.views.CiudadanoFiltroForm", return_value=form)

    view = module.CiudadanosListView()
    view.request = SimpleNamespace(GET={"q": "Juan"})

    result = view.get_queryset()
    assert result == "ordered"
    assert qs.filter.call_count >= 2


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
    redir = mocker.patch("ciudadanos.views.redirect", side_effect=lambda *a, **k: (a, k))

    invalid = view._handle_ciudadano_busqueda(request, "abc", None)
    assert invalid == "super-get"
    assert msg_warn.called

    existing = SimpleNamespace(pk=5)
    mocker.patch(
        "ciudadanos.views.Ciudadano.objects.filter",
        return_value=SimpleNamespace(first=lambda: existing),
    )
    exists_resp = view._handle_ciudadano_busqueda(request, "12345678", None)
    assert exists_resp[0][0] == "ciudadanos_editar"
    assert msg_info.called

    mocker.patch(
        "ciudadanos.views.Ciudadano.objects.filter",
        return_value=SimpleNamespace(first=lambda: None),
    )
    mocker.patch(
        "ciudadanos.views.ComedorService.obtener_datos_ciudadano_desde_renaper",
        return_value={"success": False, "message": "no"},
    )
    not_found = view._handle_ciudadano_busqueda(request, "12345678", None)
    assert not_found == "super-get"

    mocker.patch(
        "ciudadanos.views.ComedorService.obtener_datos_ciudadano_desde_renaper",
        return_value={"success": True, "data": {"documento": 123, "fecha_nacimiento": "2020-01-01"}},
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

    localidad_obj = SimpleNamespace(municipio_id=2, municipio=SimpleNamespace(provincia_id=1))
    mocker.patch(
        "ciudadanos.views.Localidad.objects.select_related",
        return_value=SimpleNamespace(filter=lambda **k: SimpleNamespace(first=lambda: localidad_obj)),
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
    view.object = SimpleNamespace(ciudadano_1=SimpleNamespace(get_absolute_url=lambda: "/base"))

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
                select_related=lambda *a, **k: SimpleNamespace(order_by=lambda *x, **y: part_qs)
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
    assert comedor_ctx == {"nominas_comedor": []}

    mocker.patch("builtins.__import__", side_effect=orig_import)
    nom_qs = _ExpedientesList([SimpleNamespace(id=7)])
    mocker.patch(
        "comedores.models.Nomina.objects.filter",
        return_value=SimpleNamespace(
            select_related=lambda *a, **k: SimpleNamespace(order_by=lambda *x, **y: nom_qs)
        ),
    )
    comedor_ok = module.CiudadanosDetailView().get_comedor_context(ciudadano)
    assert comedor_ok["nomina_actual"].id == 7


def test_ciudadanos_create_and_update_form_valid_and_context(mocker):
    create_view = module.CiudadanosCreateView()
    create_view.request = SimpleNamespace(GET={"sexo": "Z"}, user=SimpleNamespace(id=1))
    mocker.patch("django.views.generic.edit.FormMixin.get_context_data", return_value={})
    ctx = create_view.get_context_data()
    assert ctx["sexo_busqueda"] == "M"

    # get_initial consumes prefill from session
    create_view.request = SimpleNamespace(session={"ciudadano_prefill": {"nombre": "Ana"}})
    mocker.patch("django.views.generic.edit.FormMixin.get_initial", return_value={})
    initial = create_view.get_initial()
    assert initial["nombre"] == "Ana"

    ciudadano = SimpleNamespace(
        creado_por=None,
        modificado_por=None,
        save=mocker.Mock(),
        get_absolute_url=lambda: "/ciudadano/1/",
    )
    form = SimpleNamespace(save=lambda commit=False: ciudadano, save_m2m=mocker.Mock())
    create_view.request = SimpleNamespace(user=SimpleNamespace(id=2))
    mocker.patch("ciudadanos.views.messages.success")
    mocker.patch("ciudadanos.views.redirect", return_value="redir")
    assert create_view.form_valid(form) == "redir"
    assert ciudadano.creado_por.id == 2

    update_view = module.CiudadanosUpdateView()
    update_view.request = SimpleNamespace(user=SimpleNamespace(id=3))
    ciudadano2 = SimpleNamespace(modificado_por=None, save=mocker.Mock(), get_absolute_url=lambda: "/c/2/")
    form2 = SimpleNamespace(save=lambda commit=False: ciudadano2, save_m2m=mocker.Mock())
    mocker.patch("ciudadanos.views.messages.success")
    mocker.patch("ciudadanos.views.redirect", return_value="redir2")
    assert update_view.form_valid(form2) == "redir2"
    assert ciudadano2.modificado_por.id == 3
