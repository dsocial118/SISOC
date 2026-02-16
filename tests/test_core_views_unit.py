from types import SimpleNamespace

from django.db import IntegrityError
from django.test import RequestFactory

from core import views as module


class _QS:
    def __init__(self, items):
        self.items = items

    def order_by(self, *_args, **_kwargs):
        return self

    def filter(self, **kwargs):
        if "nombre__icontains" in kwargs:
            term = kwargs["nombre__icontains"].lower()
            return _QS([item for item in self.items if term in item.nombre.lower()])
        return self

    def count(self):
        return len(self.items)

    def __getitem__(self, idx):
        return self.items[idx]


def _auth_user(user_id=1):
    return SimpleNamespace(id=user_id, is_authenticated=True)


def test_parsear_datos_request_json_y_fallback():
    req_ok = SimpleNamespace(body=b'{"a": 1}', POST={})
    assert module._parsear_datos_request(req_ok)["a"] == 1

    req_bad = SimpleNamespace(body=b'{bad', POST={"x": "1"})
    assert module._parsear_datos_request(req_bad)["x"] == "1"


def test_normalizar_columnas_variantes():
    assert module._normalizar_columnas(None) is None
    assert module._normalizar_columnas("no json") is None
    assert module._normalizar_columnas([" a ", "a", "", "b"]) == ["a", "b"]


def test_columnas_preferencias_get_invalid_and_success(mocker):
    rf = RequestFactory()

    req_bad = rf.get("/core/columnas")
    req_bad.user = _auth_user()
    resp_bad = module._columnas_preferencias_get(req_bad)
    assert resp_bad.status_code == 400

    req_ok = rf.get("/core/columnas", {"list_key": "lista"})
    req_ok.user = _auth_user()
    mocker.patch(
        "core.views.PreferenciaColumnas.objects.filter",
        return_value=SimpleNamespace(only=lambda *_a, **_k: SimpleNamespace(first=lambda: SimpleNamespace(columnas=["id"]))),
    )
    resp_ok = module._columnas_preferencias_get(req_ok)
    assert resp_ok.status_code == 200


def test_columnas_preferencias_post_reset_invalid_and_success(mocker):
    rf = RequestFactory()

    req_reset = rf.post("/core/columnas", {"list_key": "l1", "reset": "1"})
    req_reset.user = _auth_user()
    delete_mock = mocker.patch(
        "core.views.PreferenciaColumnas.objects.filter",
        return_value=SimpleNamespace(delete=mocker.Mock()),
    )
    resp_reset = module._columnas_preferencias_post(req_reset)
    assert resp_reset.status_code == 200
    assert delete_mock.called

    req_invalid = rf.post("/core/columnas", {"list_key": "l2", "columns": "bad"})
    req_invalid.user = _auth_user()
    resp_invalid = module._columnas_preferencias_post(req_invalid)
    assert resp_invalid.status_code == 400

    req_ok = rf.post("/core/columnas", {"list_key": "l3", "columns": '["a","b"]'})
    req_ok.user = _auth_user()
    upsert = mocker.patch("core.views.PreferenciaColumnas.objects.update_or_create")
    resp_ok = module._columnas_preferencias_post(req_ok)
    assert resp_ok.status_code == 200
    assert upsert.called


def test_filtros_favoritos_get_paths(mocker):
    rf = RequestFactory()
    req_bad = rf.get("/core/favoritos", {"seccion": ""})
    req_bad.user = _auth_user()
    mocker.patch("core.views.obtener_configuracion_seccion", return_value=None)
    assert module._filtros_favoritos_get(req_bad).status_code == 400

    req_ok = rf.get("/core/favoritos", {"seccion": "adm"})
    req_ok.user = _auth_user()
    mocker.patch("core.views.obtener_configuracion_seccion", return_value={"x": 1})
    mocker.patch("core.views.clave_cache_filtros_favoritos", return_value="k")
    mocker.patch("core.views.cache.get", return_value=[{"id": 1}])
    resp = module._filtros_favoritos_get(req_ok)
    assert resp.status_code == 200


def test_filtros_favoritos_post_validaciones_y_success(mocker):
    rf = RequestFactory()
    user = _auth_user()

    req_dup = rf.post("/core/favoritos", {"seccion": "adm", "nombre": "A", "filtros": "[]"})
    req_dup.user = user
    mocker.patch("core.views.obtener_configuracion_seccion", return_value={"x": 1})
    mocker.patch(
        "core.views.FiltroFavorito.objects.filter",
        return_value=SimpleNamespace(exists=lambda: True),
    )
    assert module._filtros_favoritos_post(req_dup).status_code == 400

    req_obso = rf.post("/core/favoritos", {"seccion": "adm", "nombre": "B", "filtros": "[]"})
    req_obso.user = user
    mocker.patch(
        "core.views.FiltroFavorito.objects.filter",
        return_value=SimpleNamespace(exists=lambda: False),
    )
    mocker.patch("core.views.normalizar_carga", return_value=[{"a": 1}])
    mocker.patch("core.views.obtener_items_obsoletos", return_value=["old"])
    assert module._filtros_favoritos_post(req_obso).status_code == 409

    req_ok = rf.post("/core/favoritos", {"seccion": "adm", "nombre": "C", "filtros": "[]"})
    req_ok.user = user
    mocker.patch("core.views.obtener_items_obsoletos", return_value=[])
    mocker.patch(
        "core.views.FiltroFavorito.objects.create",
        return_value=SimpleNamespace(id=9, nombre="C", fecha_creacion=SimpleNamespace(isoformat=lambda: "2026-01-01")),
    )
    mocker.patch("core.views.clave_cache_filtros_favoritos", return_value="k")
    mocker.patch("core.views.cache.delete")
    resp_ok = module._filtros_favoritos_post(req_ok)
    assert resp_ok.status_code == 201

    req_int = rf.post("/core/favoritos", {"seccion": "adm", "nombre": "D", "filtros": "[]"})
    req_int.user = user
    mocker.patch("core.views.obtener_items_obsoletos", return_value=[])
    mocker.patch("core.views.FiltroFavorito.objects.create", side_effect=IntegrityError())
    assert module._filtros_favoritos_post(req_int).status_code == 400


def test_detalle_filtro_favorito_paths(mocker):
    rf = RequestFactory()
    user = _auth_user()

    req_nf = rf.get("/core/favoritos/1")
    req_nf.user = user
    mocker.patch("core.views.FiltroFavorito.objects.filter", return_value=SimpleNamespace(first=lambda: None))
    assert module.detalle_filtro_favorito(req_nf, 1).status_code == 404

    favorito = SimpleNamespace(id=1, seccion="adm", nombre="F", filtros=[{"a": 1}], delete=mocker.Mock())
    req_del = rf.delete("/core/favoritos/1")
    req_del.user = user
    mocker.patch("core.views.FiltroFavorito.objects.filter", return_value=SimpleNamespace(first=lambda: favorito))
    mocker.patch("core.views.clave_cache_filtros_favoritos", return_value="k")
    mocker.patch("core.views.cache.delete")
    assert module.detalle_filtro_favorito(req_del, 1).status_code == 200

    req_bad_sec = rf.get("/core/favoritos/1", {"seccion": "otra"})
    req_bad_sec.user = user
    mocker.patch("core.views.FiltroFavorito.objects.filter", return_value=SimpleNamespace(first=lambda: favorito))
    assert module.detalle_filtro_favorito(req_bad_sec, 1).status_code == 400


def test_load_localidad_y_load_municipios(mocker):
    rf = RequestFactory()
    user = _auth_user()

    req_m = rf.get("/core/municipios", {"provincia_id": "2"})
    req_m.user = user
    mocker.patch(
        "core.views.Municipio.objects.filter",
        return_value=SimpleNamespace(values=lambda *_a, **_k: [{"id": 1, "nombre": "M"}]),
    )
    assert module.load_municipios(req_m).status_code == 200

    req_l_none = rf.get("/core/localidades")
    req_l_none.user = user
    mocker.patch(
        "core.views.Localidad.objects.none",
        return_value=SimpleNamespace(values=lambda *_a, **_k: []),
    )
    assert module.load_localidad(req_l_none).status_code == 200

    req_l = rf.get("/core/localidades", {"municipio_id": "9"})
    req_l.user = user
    mocker.patch(
        "core.views.Localidad.objects.filter",
        return_value=SimpleNamespace(values=lambda *_a, **_k: [{"id": 1, "nombre": "L"}]),
    )
    assert module.load_localidad(req_l).status_code == 200


def test_load_organizaciones_paginado(mocker):
    rf = RequestFactory()
    req = rf.get("/core/organizaciones", {"q": "org", "page": "1"})
    req.user = _auth_user()

    items = [SimpleNamespace(id=1, nombre="Organizacion A"), SimpleNamespace(id=2, nombre="Otra")]
    mocker.patch("core.views.Organizacion.objects.all", return_value=_QS(items))

    resp = module.load_organizaciones(req)
    assert resp.status_code == 200
