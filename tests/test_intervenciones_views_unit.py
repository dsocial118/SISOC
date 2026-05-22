"""Tests unitarios para intervenciones.views."""

from types import SimpleNamespace

from intervenciones import views as module


class _Req(SimpleNamespace):
    pass


class _FilterChain:
    def __init__(self):
        self.filter_calls = []

    def filter(self, **kwargs):
        self.filter_calls.append(kwargs)
        return self

    def count(self):
        return 0


def _patch_detail_context_helpers(mocker):
    mocker.patch(
        "django.views.generic.base.ContextMixin.get_context_data",
        return_value={},
    )
    mocker.patch(
        "intervenciones.views.cache.get_or_set",
        side_effect=lambda _key, default, _timeout: default,
    )
    mocker.patch(
        "intervenciones.views.TipoIntervencion.para_programas", return_value=[]
    )
    mocker.patch(
        "intervenciones.views.TipoDestinatario.objects.all",
        return_value=[],
    )
    mocker.patch(
        "intervenciones.views.AcompanamientoService.obtener_admisiones_para_selector",
        return_value=[],
    )


def test_intervencion_detail_get_context_data_filtra_admision_validada(mocker):
    view = module.IntervencionDetailView()
    comedor = SimpleNamespace(id=7)
    admision = SimpleNamespace(id=22)
    view.kwargs = {"pk": 7}
    view.request = _Req(GET={"admision_id": "22"})

    _patch_detail_context_helpers(mocker)
    mocker.patch(
        "intervenciones.views.ComedorService.get_comedor", return_value=comedor
    )
    mocker.patch(
        "intervenciones.views.Admision.objects.filter",
        return_value=SimpleNamespace(first=lambda: admision),
    )
    intervenciones_qs = _FilterChain()
    intervencion_filter = mocker.patch(
        "intervenciones.views.Intervencion.objects.filter",
        return_value=intervenciones_qs,
    )

    ctx = view.get_context_data()

    intervencion_filter.assert_called_once_with(comedor=comedor)
    assert intervenciones_qs.filter_calls == [{"admision_id": 22}]
    assert ctx["admision_id"] == 22
    assert ctx["intervenciones"] is intervenciones_qs


def test_intervencion_detail_get_context_data_ignora_admision_ajena(mocker):
    view = module.IntervencionDetailView()
    comedor = SimpleNamespace(id=7)
    view.kwargs = {"pk": 7}
    view.request = _Req(GET={"admision_id": "22"})

    _patch_detail_context_helpers(mocker)
    mocker.patch(
        "intervenciones.views.ComedorService.get_comedor", return_value=comedor
    )
    mocker.patch(
        "intervenciones.views.Admision.objects.filter",
        return_value=SimpleNamespace(first=lambda: None),
    )
    intervenciones_qs = _FilterChain()
    intervencion_filter = mocker.patch(
        "intervenciones.views.Intervencion.objects.filter",
        return_value=intervenciones_qs,
    )

    ctx = view.get_context_data()

    intervencion_filter.assert_called_once_with(comedor=comedor)
    assert intervenciones_qs.filter_calls == []
    assert ctx["admision_id"] is None
    assert ctx["intervenciones"] is intervenciones_qs


def test_intervencion_create_form_valid_rechaza_admision_ajena(mocker):
    view = module.IntervencionCreateView()
    comedor = SimpleNamespace(id=7)
    view.kwargs = {"pk": 7}
    view.request = _Req(POST={"admision_id": "22"}, GET={})

    form = SimpleNamespace(
        instance=SimpleNamespace(),
        cleaned_data={},
        add_error=mocker.Mock(),
    )

    mocker.patch(
        "intervenciones.views.ComedorService.get_comedor", return_value=comedor
    )
    mocker.patch(
        "intervenciones.views.Admision.objects.filter",
        return_value=SimpleNamespace(first=lambda: None),
    )
    form_invalid = mocker.patch.object(view, "form_invalid", return_value="invalid")

    result = view.form_valid(form)

    assert result == "invalid"
    form.add_error.assert_called_once_with(
        None,
        "La admisión seleccionada no corresponde al comedor actual.",
    )
    form_invalid.assert_called_once_with(form)


def test_intervencion_create_form_valid_asigna_admision_validada(mocker):
    view = module.IntervencionCreateView()
    comedor = SimpleNamespace(id=7)
    admision = SimpleNamespace(id=22)
    view.kwargs = {"pk": 7}
    view.request = _Req(POST={"admision_id": "22"}, GET={})

    form = SimpleNamespace(
        instance=SimpleNamespace(save=mocker.Mock()),
        cleaned_data={},
        add_error=mocker.Mock(),
    )

    mocker.patch(
        "intervenciones.views.ComedorService.get_comedor", return_value=comedor
    )
    mocker.patch(
        "intervenciones.views.Admision.objects.filter",
        return_value=SimpleNamespace(first=lambda: admision),
    )
    mocker.patch(
        "intervenciones.views.reverse",
        side_effect=lambda name, kwargs=None, **_k: f"/{name}/{kwargs['pk']}",
    )
    mocker.patch("intervenciones.views.safe_redirect", return_value="redir")

    result = view.form_valid(form)

    assert result == "redir"
    assert form.instance.admision is admision
    form.instance.save.assert_called_once()
    form.add_error.assert_not_called()
