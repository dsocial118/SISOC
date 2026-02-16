from types import SimpleNamespace

from relevamientos.helpers import RelevamientoFormManager
from relevamientos.views.web_views import (
    RelevamientoCreateView,
    RelevamientoDeleteView,
    RelevamientoDetailView,
    RelevamientoListView,
    RelevamientoUpdateView,
)


def _forms_context():
    return {name: SimpleNamespace() for name in RelevamientoFormManager.FORM_CLASSES}


def test_create_view_get_form_kwargs_agrega_comedor_pk(mocker):
    view = RelevamientoCreateView()
    view.kwargs = {"comedor_pk": 77}
    mocker.patch(
        "django.views.generic.edit.ModelFormMixin.get_form_kwargs",
        return_value={"base": True},
    )

    kwargs = view.get_form_kwargs()

    assert kwargs["base"] is True
    assert kwargs["comedor_pk"] == 77


def test_create_view_get_context_data_construye_forms_y_comedor(mocker):
    view = RelevamientoCreateView()
    view.request = SimpleNamespace(method="POST", POST={"x": 1})
    view.kwargs = {"comedor_pk": 7}
    mocker.patch("django.views.generic.edit.FormMixin.get_context_data", return_value={"base": 1})
    mocker.patch(
        "relevamientos.views.web_views.RelevamientoFormManager.build_forms",
        return_value={"relevamiento_form": "FORM"},
    )
    mocker.patch(
        "relevamientos.views.web_views.RelevamientoFormManager.get_comedor_context",
        return_value={"id": 7},
    )

    ctx = view.get_context_data()

    assert ctx["base"] == 1
    assert ctx["comedor"] == {"id": 7}
    assert ctx["relevamiento_form"] == "FORM"


def test_create_view_error_message_reporta_forms_invalidos(mocker):
    view = RelevamientoCreateView()
    view.request = SimpleNamespace()
    messages_error = mocker.patch("relevamientos.views.web_views.messages.error")
    forms = {
        "a": SimpleNamespace(is_valid=lambda: False, errors={"f": ["x"]}),
        "b": SimpleNamespace(is_valid=lambda: True, errors={}),
    }

    view.error_message(forms)

    messages_error.assert_called_once()


def test_create_view_form_valid_redirige_si_forms_validos(mocker):
    view = RelevamientoCreateView()
    view.request = SimpleNamespace()
    view._context_data = _forms_context()
    mocker.patch("relevamientos.views.web_views.RelevamientoFormManager.validate_forms", return_value={"ok": True})
    mocker.patch("relevamientos.views.web_views.RelevamientoFormManager.all_valid", return_value=True)
    mocker.patch(
        "relevamientos.views.web_views.RelevamientoService.populate_relevamiento",
        return_value=SimpleNamespace(id=55, comedor=SimpleNamespace(id=23)),
    )
    redirect_mock = mocker.patch("relevamientos.views.web_views.redirect", return_value="REDIRECTED")

    result = view.form_valid(form=SimpleNamespace())

    assert result == "REDIRECTED"
    redirect_mock.assert_called_once_with("relevamiento_detalle", comedor_pk=23, pk=55)


def test_create_view_form_valid_muestra_errores_si_forms_invalidos(mocker):
    view = RelevamientoCreateView()
    view.request = SimpleNamespace()
    view._context_data = _forms_context()
    validation_results = {"any": False}
    mocker.patch("relevamientos.views.web_views.RelevamientoFormManager.validate_forms", return_value=validation_results)
    mocker.patch("relevamientos.views.web_views.RelevamientoFormManager.all_valid", return_value=False)
    show_errors = mocker.patch("relevamientos.views.web_views.RelevamientoFormManager.show_form_errors")
    view.form_invalid = mocker.Mock(return_value="INVALID")

    result = view.form_valid(form=SimpleNamespace())

    assert result == "INVALID"
    show_errors.assert_called_once()


def test_list_view_get_queryset_filtra_y_ordena(mocker):
    view = RelevamientoListView()
    view.kwargs = {"comedor_pk": 5}
    values_mock = mocker.Mock(return_value=[{"id": 1}])
    order_by_mock = mocker.Mock(return_value=SimpleNamespace(values=values_mock))
    filter_mock = mocker.patch(
        "relevamientos.views.web_views.Relevamiento.objects.filter",
        return_value=SimpleNamespace(order_by=order_by_mock),
    )

    result = view.get_queryset()

    assert result == [{"id": 1}]
    filter_mock.assert_called_once_with(comedor=5)
    order_by_mock.assert_called_once_with("-estado", "-id")
    values_mock.assert_called_once_with("id", "fecha_visita", "estado")


def test_list_view_get_context_data_agrega_comedor(mocker):
    view = RelevamientoListView()
    view.kwargs = {"comedor_pk": 5}
    mocker.patch(
        "django.views.generic.list.MultipleObjectMixin.get_context_data",
        return_value={"relevamientos": []},
    )
    get_mock = mocker.Mock(return_value={"id": 5, "nombre": "C"})
    values_mock = mocker.Mock(return_value=SimpleNamespace(get=get_mock))
    mocker.patch("relevamientos.views.web_views.Comedor.objects.values", values_mock)

    context = view.get_context_data()

    assert context["comedor"]["id"] == 5
    values_mock.assert_called_once_with(
        "id",
        "nombre",
        "provincia__nombre",
        "localidad__nombre",
        "municipio__nombre",
    )


def test_update_view_get_context_data_construye_instance_map(mocker):
    view = RelevamientoUpdateView()
    view.request = SimpleNamespace(method="GET", POST={})
    view.kwargs = {"comedor_pk": 10}
    view.object = SimpleNamespace(
        espacio=SimpleNamespace(cocina="COCINA", prestacion="EPREST"),
        responsable="RESP",
    )
    mocker.patch("django.views.generic.edit.FormMixin.get_context_data", return_value={"base": 1})
    build_forms = mocker.patch(
        "relevamientos.views.web_views.RelevamientoFormManager.build_forms",
        return_value={"relevamiento_form": "FORM"},
    )
    mocker.patch(
        "relevamientos.views.web_views.RelevamientoFormManager.get_comedor_context",
        return_value={"id": 10},
    )

    context = view.get_context_data()

    assert context["base"] == 1
    assert context["comedor"] == {"id": 10}
    assert context["responsable"] == "RESP"
    assert view._context_data == context
    assert "instance_map" in build_forms.call_args.kwargs
    assert build_forms.call_args.kwargs["instance_map"]["espacio_cocina_form"] == "COCINA"


def test_update_view_get_form_kwargs_agrega_comedor_pk(mocker):
    view = RelevamientoUpdateView()
    view.kwargs = {"comedor_pk": 18}
    mocker.patch(
        "django.views.generic.edit.ModelFormMixin.get_form_kwargs",
        return_value={"k": 1},
    )

    kwargs = view.get_form_kwargs()

    assert kwargs["k"] == 1
    assert kwargs["comedor_pk"] == 18


def test_update_view_form_valid_redirige_y_error_message(mocker):
    view = RelevamientoUpdateView()
    view.request = SimpleNamespace()
    view._context_data = _forms_context()
    mocker.patch(
        "relevamientos.views.web_views.RelevamientoFormManager.validate_forms",
        return_value={"ok": True},
    )
    mocker.patch(
        "relevamientos.views.web_views.RelevamientoFormManager.all_valid",
        return_value=True,
    )
    mocker.patch(
        "relevamientos.views.web_views.RelevamientoService.populate_relevamiento",
        return_value=SimpleNamespace(id=9, comedor=SimpleNamespace(id=2)),
    )
    redirect_mock = mocker.patch("relevamientos.views.web_views.redirect", return_value="OK")

    result = view.form_valid(SimpleNamespace())

    assert result == "OK"
    redirect_mock.assert_called_once_with("relevamiento_detalle", comedor_pk=2, pk=9)

    msg = mocker.patch("relevamientos.views.web_views.messages.error")
    view.error_message(
        {
            "x": SimpleNamespace(is_valid=lambda: False, errors={"a": ["b"]}),
            "y": SimpleNamespace(is_valid=lambda: True, errors={}),
        }
    )
    msg.assert_called_once()


def test_detail_view_get_context_data_sin_relaciones_retorna_none(mocker):
    view = RelevamientoDetailView()
    relevamiento = SimpleNamespace(
        id=4,
        comedor=SimpleNamespace(id=50),
        prestacion=None,
        espacio=None,
        recursos=None,
        punto_entregas=None,
    )
    view.object = relevamiento
    timeline = [SimpleNamespace(id=4, fecha_visita="2024-01-01", estado=None)]
    mocker.patch(
        "django.views.generic.detail.SingleObjectMixin.get_context_data",
        return_value={},
    )
    mocker.patch(
        "relevamientos.views.web_views.Relevamiento.objects.filter",
        return_value=SimpleNamespace(
            only=lambda *a, **k: SimpleNamespace(order_by=lambda *x, **y: timeline)
        ),
    )

    context = view.get_context_data()

    assert context["relevamiento_data"]["gas"] is None
    assert context["relevamiento_data"]["Entregas"] is None
    assert context["relevamientos_timeline"][0]["estado"] == "Sin información"


def test_detail_view_get_context_data_limita_timeline_y_agrega_datos(mocker):
    view = RelevamientoDetailView()
    relevamiento = SimpleNamespace(
        id=2,
        comedor=SimpleNamespace(id=99),
        prestacion="PREST",
        espacio=SimpleNamespace(
            cocina=SimpleNamespace(
                abastecimiento_combustible=SimpleNamespace(all=lambda: [1, 2])
            )
        ),
        recursos=SimpleNamespace(
            recursos_donaciones_particulares=SimpleNamespace(all=lambda: [1]),
            recursos_estado_nacional=SimpleNamespace(all=lambda: [1]),
            recursos_estado_provincial=SimpleNamespace(all=lambda: [1]),
            recursos_estado_municipal=SimpleNamespace(all=lambda: [1]),
            recursos_otros=SimpleNamespace(all=lambda: [1]),
        ),
        punto_entregas=SimpleNamespace(
            frecuencia_recepcion_mercaderias=SimpleNamespace(all=lambda: [1])
        ),
    )
    view.object = relevamiento
    timeline = [
        SimpleNamespace(id=1, fecha_visita="2024-01-01", estado="Pendiente"),
        SimpleNamespace(id=2, fecha_visita="2024-01-02", estado="Finalizado"),
        SimpleNamespace(id=3, fecha_visita="2024-01-03", estado="Visita pendiente"),
        SimpleNamespace(id=4, fecha_visita="2024-01-04", estado="Otro"),
    ]
    mocker.patch("django.views.generic.detail.SingleObjectMixin.get_context_data", return_value={})
    filter_mock = mocker.patch(
        "relevamientos.views.web_views.Relevamiento.objects.filter",
        return_value=SimpleNamespace(
            only=lambda *a, **k: SimpleNamespace(order_by=lambda *x, **y: timeline)
        ),
    )
    mocker.patch(
        "relevamientos.views.web_views.RelevamientoService.separate_string",
        side_effect=lambda values: f"S-{len(list(values))}",
    )

    context = view.get_context_data()

    assert context["prestacion"] == "PREST"
    assert len(context["relevamientos_timeline"]) == 3
    assert any(item["card_class"] == "active" for item in context["relevamientos_timeline"])
    assert context["relevamiento_data"]["gas"] == "S-2"
    filter_mock.assert_called_once_with(comedor=relevamiento.comedor)


def test_detail_view_get_object_usa_relaciones_optimizadas(mocker):
    view = RelevamientoDetailView()
    view.kwargs = {"pk": 44}
    get_mock = mocker.Mock(return_value="OBJ")
    prefetch_mock = mocker.Mock(return_value=SimpleNamespace(get=get_mock))
    select_mock = mocker.patch(
        "relevamientos.views.web_views.Relevamiento.objects.select_related",
        return_value=SimpleNamespace(prefetch_related=prefetch_mock),
    )

    result = view.get_object()

    assert result == "OBJ"
    assert select_mock.called
    assert prefetch_mock.called
    get_mock.assert_called_once_with(pk=44)


def test_delete_view_get_success_url_redirige_a_comedor_detalle():
    view = RelevamientoDeleteView()
    view.object = SimpleNamespace(comedor=SimpleNamespace(id=8))

    result = str(view.get_success_url())

    assert result.endswith("/comedores/8")
