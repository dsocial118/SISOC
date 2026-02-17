"""Tests unitarios para celiaquia.views.legajo_editar."""

import contextlib
import json
from datetime import date
from types import SimpleNamespace

from celiaquia.views import legajo_editar as module


class _Groups:
    def __init__(self, names=None):
        self.names = set(names or [])
        self.last = None

    def filter(self, name):
        self.last = name
        return self

    def exists(self):
        return self.last in self.names


def _user(auth=True, superuser=False, groups=None, provincial=False):
    profile = SimpleNamespace(es_usuario_provincial=provincial, provincia_id=1 if provincial else None)
    return SimpleNamespace(
        is_authenticated=auth,
        is_superuser=superuser,
        groups=_Groups(groups),
        profile=profile,
        username="tester",
    )


def _build_legajo():
    ciudadano = SimpleNamespace(
        apellido="Perez",
        nombre="Ana",
        documento="123",
        fecha_nacimiento=date(2000, 1, 1),
        sexo=SimpleNamespace(id=1),
        sexo_id=1,
        nacionalidad_id=2,
        telefono="12345678",
        email="a@a.com",
        calle="Mitre",
        altura="10",
        codigo_postal="1900",
        municipio=SimpleNamespace(id=3),
        municipio_id=3,
        localidad=SimpleNamespace(id=4),
        localidad_id=4,
        save=lambda: None,
    )
    return SimpleNamespace(pk=11, ciudadano=ciudadano)


def test_helpers_user_group_admin_provincial():
    u = _user(groups={"TecnicoCeliaquia"})
    assert module._user_in_group(u, "TecnicoCeliaquia") is True
    assert module._is_admin(_user(superuser=True)) is True
    assert module._is_provincial(_user(provincial=True)) is True
    assert module._is_provincial(SimpleNamespace()) is False


def test_get_permission_denied_paths(mocker):
    view = module.EditarLegajoView()

    exp = SimpleNamespace(estado=SimpleNamespace(nombre="ENVIADO"))
    legajo = _build_legajo()
    mocker.patch("celiaquia.views.legajo_editar.get_object_or_404", side_effect=[exp, legajo])

    # usuario sin permisos
    req = SimpleNamespace(user=_user())
    out = view.get(req, pk=1, legajo_id=2)
    assert out.status_code == 403

    # provincial con estado no editable
    mocker.patch("celiaquia.views.legajo_editar.get_object_or_404", side_effect=[exp, legajo])
    req_prov = SimpleNamespace(user=_user(provincial=True))
    out_prov = view.get(req_prov, pk=1, legajo_id=2)
    assert out_prov.status_code == 403


def test_get_success_returns_legajo_data(mocker):
    view = module.EditarLegajoView()
    exp = SimpleNamespace(estado=SimpleNamespace(nombre="CREADO"))
    legajo = _build_legajo()

    mocker.patch("celiaquia.views.legajo_editar.get_object_or_404", side_effect=[exp, legajo])
    req = SimpleNamespace(user=_user(groups={"TecnicoCeliaquia"}))

    out = view.get(req, pk=1, legajo_id=2)
    body = json.loads(out.content)
    assert body["success"] is True
    assert body["legajo"]["apellido"] == "Perez"


def test_post_validation_error_and_internal_error(mocker):
    view = module.EditarLegajoView()
    exp = SimpleNamespace(estado=SimpleNamespace(nombre="CREADO"))
    legajo = _build_legajo()

    mocker.patch("celiaquia.views.legajo_editar.get_object_or_404", side_effect=[exp, legajo])
    mocker.patch(
        "celiaquia.views.legajo_editar.transaction.atomic",
        return_value=contextlib.nullcontext(),
    )

    # faltan obligatorios
    req_bad = SimpleNamespace(
        user=_user(groups={"TecnicoCeliaquia"}),
        POST={"apellido": "", "nombre": "", "documento": ""},
    )
    out_bad = view.post(req_bad, pk=1, legajo_id=2)
    assert out_bad.status_code == 400

    # error interno al guardar
    legajo2 = _build_legajo()
    legajo2.ciudadano.save = lambda: (_ for _ in ()).throw(RuntimeError("boom"))
    mocker.patch("celiaquia.views.legajo_editar.get_object_or_404", side_effect=[exp, legajo2])
    mocker.patch("celiaquia.views.legajo_editar.Sexo.objects.get", return_value=SimpleNamespace(id=1))
    mocker.patch("celiaquia.views.legajo_editar.Nacionalidad.objects.get", return_value=SimpleNamespace(id=2))
    mocker.patch("core.models.Municipio.objects.get", return_value=SimpleNamespace(id=3))
    mocker.patch("core.models.Localidad.objects.get", return_value=SimpleNamespace(id=4))

    req_err = SimpleNamespace(
        user=_user(groups={"TecnicoCeliaquia"}),
        POST={
            "apellido": "P",
            "nombre": "N",
            "documento": "123",
            "fecha_nacimiento": "2000-01-01",
            "sexo": "1",
            "nacionalidad": "2",
            "telefono": "12345678",
            "email": "a@a.com",
            "calle": "Mitre",
            "altura": "10",
            "codigo_postal": "1900",
            "municipio": "3",
            "localidad": "4",
        },
    )
    out_err = view.post(req_err, pk=1, legajo_id=2)
    assert out_err.status_code == 500


def test_post_success(mocker):
    view = module.EditarLegajoView()
    exp = SimpleNamespace(estado=SimpleNamespace(nombre="CREADO"))
    legajo = _build_legajo()
    saved = {"ok": False}

    def _save():
        saved["ok"] = True

    legajo.ciudadano.save = _save

    mocker.patch("celiaquia.views.legajo_editar.get_object_or_404", side_effect=[exp, legajo])
    mocker.patch(
        "celiaquia.views.legajo_editar.transaction.atomic",
        return_value=contextlib.nullcontext(),
    )
    mocker.patch("celiaquia.views.legajo_editar.Sexo.objects.get", return_value=SimpleNamespace(id=1))
    mocker.patch("celiaquia.views.legajo_editar.Nacionalidad.objects.get", return_value=SimpleNamespace(id=2))
    mocker.patch("core.models.Municipio.objects.get", return_value=SimpleNamespace(id=3))
    mocker.patch("core.models.Localidad.objects.get", return_value=SimpleNamespace(id=4))

    req = SimpleNamespace(
        user=_user(groups={"TecnicoCeliaquia"}),
        POST={
            "apellido": "P",
            "nombre": "N",
            "documento": "123",
            "fecha_nacimiento": "2000-01-01",
            "sexo": "1",
            "nacionalidad": "2",
            "telefono": "12345678",
            "email": "a@a.com",
            "calle": "Mitre",
            "altura": "10",
            "codigo_postal": "1900",
            "municipio": "3",
            "localidad": "4",
        },
    )

    out = view.post(req, pk=1, legajo_id=2)
    body = json.loads(out.content)
    assert out.status_code == 200
    assert body["success"] is True
    assert saved["ok"] is True
