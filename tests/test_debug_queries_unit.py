"""Tests for test debug queries unit."""

from types import SimpleNamespace

from core import debug_queries as module


def _patch_fake_connection(mocker, queries=None):
    fake = SimpleNamespace(queries=list(queries or []))
    mocker.patch.object(module, "connection", fake)
    mocker.patch.object(module, "reset_queries", side_effect=lambda: fake.queries.clear())
    return fake


def test_show_query_analysis_logs_select_insert_update(mocker):
    _patch_fake_connection(
        mocker,
        [
            {"sql": "SELECT * FROM x", "time": "0.10"},
            {"sql": "INSERT INTO x", "time": "0.20"},
            {"sql": "UPDATE x SET y=1", "time": "0.05"},
        ],
    )
    log = mocker.patch.object(module, "logger")

    module.show_query_analysis()

    assert log.info.call_count >= 5


def test_debug_view_queries_detail_and_list_paths(mocker):
    fake_conn = _patch_fake_connection(mocker)

    class Obj:
        id = 7

    class Model:
        class objects:
            @staticmethod
            def first():
                return Obj()

            @staticmethod
            def filter(pk=None):
                return SimpleNamespace(first=lambda: Obj())

    class DetailView:
        def setup(self, request, **kwargs):
            pass

        def get_object(self):
            fake_conn.queries.append({"sql": "SELECT 1", "time": "0.01"})
            return Obj()

        def get_context_data(self, object=None):
            fake_conn.queries.append({"sql": "SELECT 2", "time": "0.01"})
            return {}

    class ListView:
        def setup(self, request, **kwargs):
            pass

        def get_queryset(self):
            fake_conn.queries.append({"sql": "SELECT 3", "time": "0.01"})
            return [Obj()]

        def get_context_data(self, object_list=None):
            fake_conn.queries.append({"sql": "SELECT 4", "time": "0.01"})
            return {}

    mocker.patch.object(module, "RequestFactory", return_value=SimpleNamespace(get=lambda _: SimpleNamespace()))
    mocker.patch.object(module.User.objects, "get", return_value=object())

    ok, count = module.debug_view_queries(DetailView, "/x/{pk}/", Model, "Detail", pk=True, pk_kwarg="pk")
    assert (ok, count) == (True, 2)

    ok, count = module.debug_view_queries(ListView, "/x/", Model, "List", pk=False)
    assert (ok, count) == (True, 2)


def test_debug_ciudadano_detail_queries_success_and_failure(mocker):
    fake_conn = _patch_fake_connection(mocker)
    ciudadano = SimpleNamespace(id=1, nombre="A", apellido="B")
    mocker.patch.object(module.Ciudadano.objects, "first", return_value=ciudadano)
    mocker.patch.object(module, "RequestFactory", return_value=SimpleNamespace(get=lambda _: SimpleNamespace()))
    mocker.patch.object(module.User.objects, "get", return_value=object())

    class View:
        def setup(self, request, **kwargs):
            pass

        def get_object(self):
            fake_conn.queries.append({"sql": "SELECT 1", "time": "0.01"})
            return ciudadano

        def get_context_data(self, object=None):
            fake_conn.queries.append({"sql": "SELECT 2", "time": "0.01"})
            return {"familia": [1]}

    mocker.patch.object(module, "CiudadanosDetailView", View)
    assert module.debug_ciudadano_detail_queries() is True

    mocker.patch.object(module.Ciudadano.objects, "first", side_effect=RuntimeError("x"))
    assert module.debug_ciudadano_detail_queries() is False


def test_debug_all_views_aggregates_results_and_import_error_branch(mocker):
    mocker.patch.object(module, "debug_view_queries", return_value=(True, 11))

    results = module.debug_all_views()
    assert results["CiudadanosDetailView"] == 11
    assert results["ComedorListView"] == 11

    original_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "duplas.views":
            raise ImportError("blocked")
        return original_import(name, *args, **kwargs)

    mocker.patch("builtins.__import__", side_effect=fake_import)
    results2 = module.debug_all_views()
    assert "CiudadanosDetailView" in results2
