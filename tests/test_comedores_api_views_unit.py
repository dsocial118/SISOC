"""Tests unitarios para helpers de comedores.api_views."""

from datetime import date, datetime
from types import SimpleNamespace

from comedores import api_views as module


def _build_view(request=None):
    view = module.ComedorDetailViewSet()
    view.request = request or SimpleNamespace(user=None)
    return view


def test_get_scoped_comedor_ids_pwa_and_non_pwa(mocker):
    user = object()
    view = _build_view(SimpleNamespace(user=user))

    mocker.patch("comedores.api_views.is_pwa_user", return_value=True)
    mocker.patch("comedores.api_views.get_accessible_comedor_ids", return_value=[1, 2])
    assert view._get_scoped_comedor_ids() == [1, 2]

    mocker.patch("comedores.api_views.is_pwa_user", return_value=False)
    mocker.patch(
        "comedores.api_views.ComedorService.get_filtered_comedores",
        return_value=[{"id": 9}, {"id": 10}],
    )
    assert view._get_scoped_comedor_ids() == [9, 10]


def test_list_pwa_and_non_pwa_paths(mocker):
    user = object()
    req = SimpleNamespace(user=user)
    view = _build_view(req)

    # rama pwa
    mocker.patch("comedores.api_views.is_pwa_user", return_value=True)
    mocker.patch.object(view, "_get_scoped_comedor_ids", return_value=[1])
    qs = SimpleNamespace(filter=lambda **_k: [{"id": 1}])
    svc = mocker.patch(
        "comedores.api_views.ComedorService.get_filtered_comedores", return_value=qs
    )
    mocker.patch.object(view, "paginate_queryset", return_value=None)

    resp = view.list(req)
    assert resp.status_code == 200
    assert resp.data == [{"id": 1}]
    assert svc.called

    # rama no pwa con paginación
    mocker.patch("comedores.api_views.is_pwa_user", return_value=False)
    mocker.patch(
        "comedores.api_views.ComedorService.get_filtered_comedores",
        return_value=[{"id": 2}],
    )
    mocker.patch.object(view, "paginate_queryset", return_value=[{"id": 2}])
    mocker.patch.object(view, "get_paginated_response", return_value="paginated")

    out = view.list(req)
    assert out == "paginated"


def test_parse_period_date_and_coerce_datetime(mocker):
    view = _build_view()

    assert view._parse_period_date("2025-01-15") == date(2025, 1, 15)
    assert view._parse_period_date("2025-01") == date(2025, 1, 1)
    assert view._parse_period_date("2025-01", is_end=True) == date(2025, 1, 31)
    assert view._parse_period_date("bad") is None
    assert view._parse_period_date(None) is None

    dt = datetime(2025, 1, 1, 10, 0, 0)
    aware = datetime(2025, 1, 1, 10, 0, 0)
    mocker.patch("comedores.api_views.timezone.is_naive", return_value=True)
    mocker.patch("comedores.api_views.make_aware", return_value=aware)
    assert view._coerce_datetime(dt) == aware

    mocker.patch("comedores.api_views.timezone.is_naive", return_value=False)
    assert view._coerce_datetime(dt) == dt


def test_build_absolute_url_and_file_path_non_fieldfile():
    view = _build_view()
    assert view._build_absolute_url(None, "x") is None
    assert view._file_path_from_field("x") is None


def test_collect_documentos_aggregates_multiple_sources(mocker):
    view = _build_view()
    mocker.patch.object(view, "_build_absolute_url", return_value="http://x")
    mocker.patch.object(view, "_file_path_from_field", return_value="/tmp/f")
    mocker.patch.object(view, "_coerce_datetime", side_effect=lambda v: v)

    image = SimpleNamespace(id=2, imagen=SimpleNamespace(name="imgfile.jpg"))
    intervencion = SimpleNamespace(
        id=3,
        documentacion=SimpleNamespace(name="interv.pdf"),
        fecha="2025-01-01",
    )
    doc_final = SimpleNamespace(
        id=4,
        documento=SimpleNamespace(name="final.pdf"),
        fecha_modificacion="2025-01-02",
        tipo=SimpleNamespace(nombre="final"),
    )
    adjunto = SimpleNamespace(
        id=5,
        archivo=SimpleNamespace(name="mensual.pdf"),
        ultima_modificacion="2025-01-03",
    )
    rendicion = SimpleNamespace(arvhios_adjuntos=SimpleNamespace(all=lambda: [adjunto]))

    mocker.patch(
        "comedores.api_views.Intervencion.objects.filter",
        return_value=SimpleNamespace(
            only=lambda *_a: SimpleNamespace(order_by=lambda *_b: [intervencion])
        ),
    )
    mocker.patch(
        "comedores.api_views.DocumentoRendicionFinal.objects.filter",
        return_value=SimpleNamespace(
            select_related=lambda *_a: SimpleNamespace(
                only=lambda *_b: SimpleNamespace(order_by=lambda *_c: [doc_final])
            )
        ),
    )

    rendiciones_mgr = SimpleNamespace(
        prefetch_related=lambda *_a: SimpleNamespace(
            all=lambda: SimpleNamespace(order_by=lambda *_b: [rendicion])
        )
    )

    comedor = SimpleNamespace(
        id=1,
        foto_legajo=SimpleNamespace(name="legajo.pdf"),
        fecha_creacion="2025-01-01",
        imagenes_optimized=[image],
        rendiciones_cuentas_mensuales=rendiciones_mgr,
        imagenes=SimpleNamespace(all=lambda: []),
    )

    docs = view._collect_documentos(
        comedor, request=SimpleNamespace(build_absolute_uri=lambda u: f"http://host{u}")
    )
    tipos = {doc["tipo"] for doc in docs}
    assert "foto_legajo" in tipos
    assert "imagen_comedor" in tipos
    assert "documentacion_intervencion" in tipos
    assert "final" in tipos
    assert "documento_rendicion_mensual" in tipos
