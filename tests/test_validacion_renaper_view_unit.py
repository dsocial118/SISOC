"""Tests unitarios para celiaquia.views.validacion_renaper."""

import json
from types import SimpleNamespace

import pytest
from django.core.exceptions import PermissionDenied

from celiaquia.views import validacion_renaper as module


class _Groups:
    def __init__(self, allowed=None):
        self.allowed = allowed or set()
        self.last_name = None

    def filter(self, name):
        self.last_name = name
        return self

    def exists(self):
        return self.last_name in self.allowed


class _User:
    def __init__(self, auth=True, superuser=False, groups=None, user_id=10):
        self.is_authenticated = auth
        self.is_superuser = superuser
        self.groups = groups or _Groups()
        self.id = user_id

    def get_username(self):
        return "tester"


class _Asignaciones:
    def __init__(self, assigned=True):
        self.assigned = assigned

    def filter(self, tecnico):
        return SimpleNamespace(exists=lambda: self.assigned)


class _Legajo:
    def __init__(self, ciudadano=None, assigned=True):
        self.pk = 1
        self.expediente_id = 100
        self.estado_validacion_renaper = None
        self.subsanacion_motivo = None
        self.revision_tecnico = None
        self.saved_fields = None
        self.ciudadano = ciudadano
        self.expediente = SimpleNamespace(asignaciones_tecnicos=_Asignaciones(assigned))

    def save(self, update_fields=None):
        self.saved_fields = update_fields


@pytest.mark.parametrize(
    "value,length,expected",
    [
        ("abc", 10, "abc"),
        ("a" * 8, 5, "aaaaa…"),
        (123, 5, 123),
    ],
)
def test_helpers_truncate(value, length, expected):
    assert module._truncate(value, length) == expected


def test_helpers_build_log_data_and_in_group():
    user = _User(groups=_Groups({"TecnicoCeliaquia"}))
    legajo = SimpleNamespace(pk=2, expediente_id=20)
    ciudadano = SimpleNamespace(id=30, sexo=SimpleNamespace(sexo="Masculino"))

    data = module._build_log_data(
        user,
        legajo,
        ciudadano,
        documento_original="20123456780",
        documento_consulta="12345678",
        sexo_renaper="M",
    )

    assert data["user_id"] == 10
    assert data["legajo_id"] == 2
    assert data["documento_consulta"] == "12345678"
    assert module._in_group(user, "TecnicoCeliaquia") is True
    assert module._in_group(user, "NoExiste") is False


def test_dispatch_permissions():
    view = module.ValidacionRenaperView()
    with pytest.raises(PermissionDenied):
        view.dispatch(SimpleNamespace(user=_User(auth=False)))

    with pytest.raises(PermissionDenied):
        view.dispatch(SimpleNamespace(user=_User(groups=_Groups())))


def test_guardar_validacion_estado_paths(mocker):
    view = module.ValidacionRenaperView()
    req = SimpleNamespace(user=_User(), POST={"comentario": "corregir"})
    legajo = _Legajo()
    mocker.patch("celiaquia.views.validacion_renaper.get_object_or_404", return_value=legajo)

    invalid = view._guardar_validacion_estado(req, pk=1, legajo_id=2, validacion_estado="9")
    body_invalid = json.loads(invalid.content)
    assert body_invalid["success"] is False

    subsanar = view._guardar_validacion_estado(req, pk=1, legajo_id=2, validacion_estado="3")
    body_subsanar = json.loads(subsanar.content)
    assert body_subsanar["success"] is True
    assert legajo.revision_tecnico == "SUBSANAR"
    assert "subsanacion_motivo" in legajo.saved_fields

    mocker.patch("celiaquia.views.validacion_renaper.get_object_or_404", side_effect=RuntimeError("boom"))
    err = view._guardar_validacion_estado(req, pk=1, legajo_id=2, validacion_estado="1")
    assert err.status_code == 500


def test_consultar_renaper_guard_clauses(mocker):
    view = module.ValidacionRenaperView()
    tecnico = _User(groups=_Groups({"TecnicoCeliaquia"}))

    # técnico no asignado
    legajo_no_asig = _Legajo(ciudadano=SimpleNamespace(documento="12345678"), assigned=False)
    mocker.patch(
        "celiaquia.views.validacion_renaper.get_object_or_404", return_value=legajo_no_asig
    )
    resp_forbidden = view._consultar_renaper(SimpleNamespace(user=tecnico), pk=1, legajo_id=1)
    assert resp_forbidden.status_code == 403

    # ciudadano inexistente
    legajo_sin_ciudadano = _Legajo(ciudadano=None, assigned=True)
    mocker.patch(
        "celiaquia.views.validacion_renaper.get_object_or_404", return_value=legajo_sin_ciudadano
    )
    resp_no_cit = view._consultar_renaper(SimpleNamespace(user=_User(superuser=True)), pk=1, legajo_id=1)
    assert json.loads(resp_no_cit.content)["success"] is False

    # documento inválido
    citizen = SimpleNamespace(
        documento="abc",
        sexo=SimpleNamespace(sexo="Masculino"),
        nombre="ana",
        apellido="perez",
        fecha_nacimiento=None,
        calle="",
        altura=None,
        piso_departamento="",
        ciudad="",
        provincia=None,
        codigo_postal=None,
    )
    legajo_bad_doc = _Legajo(ciudadano=citizen, assigned=True)
    mocker.patch(
        "celiaquia.views.validacion_renaper.get_object_or_404", return_value=legajo_bad_doc
    )
    resp_bad_doc = view._consultar_renaper(SimpleNamespace(user=_User(superuser=True)), pk=1, legajo_id=1)
    assert "DNI válido" in json.loads(resp_bad_doc.content)["error"]


def test_consultar_renaper_remote_error_fallecido_and_success(mocker):
    view = module.ValidacionRenaperView()
    base_ciudadano = dict(
        documento="20123456780",
        sexo=SimpleNamespace(sexo="Masculino"),
        nombre="ana",
        apellido="perez",
        fecha_nacimiento=None,
        calle="mitre",
        altura=10,
        piso_departamento="1a",
        ciudad="la plata",
        provincia=None,
        codigo_postal=1900,
    )

    # Fallecido
    legajo_fall = _Legajo(ciudadano=SimpleNamespace(**base_ciudadano))
    mocker.patch("celiaquia.views.validacion_renaper.get_object_or_404", return_value=legajo_fall)
    mocker.patch(
        "celiaquia.views.validacion_renaper.consultar_datos_renaper",
        return_value={"success": True, "fallecido": True, "data": {}},
    )
    r1 = view._consultar_renaper(SimpleNamespace(user=_User(superuser=True)), pk=1, legajo_id=1)
    assert "fallecida" in json.loads(r1.content)["error"]

    # Error remoto
    legajo_err = _Legajo(ciudadano=SimpleNamespace(**base_ciudadano))
    mocker.patch("celiaquia.views.validacion_renaper.get_object_or_404", return_value=legajo_err)
    mocker.patch(
        "celiaquia.views.validacion_renaper.consultar_datos_renaper",
        return_value={"success": False, "error": "x", "raw_response": "raw"},
    )
    r2 = view._consultar_renaper(SimpleNamespace(user=_User(superuser=True)), pk=1, legajo_id=1)
    assert "Cuit o el Sexo" in json.loads(r2.content)["error"]

    # Éxito + mapeo provincia por id
    legajo_ok = _Legajo(ciudadano=SimpleNamespace(**base_ciudadano))
    mocker.patch("celiaquia.views.validacion_renaper.get_object_or_404", return_value=legajo_ok)
    mocker.patch(
        "celiaquia.views.validacion_renaper.consultar_datos_renaper",
        return_value={
            "success": True,
            "fallecido": False,
            "data": {
                "documento": "12345678",
                "nombre": "ANA",
                "apellido": "PEREZ",
                "fecha_nacimiento": "2000-01-02",
                "calle": "MITRE",
                "altura": "10",
                "piso_departamento": "1A",
                "ciudad": "LA PLATA",
                "provincia": 1,
                "codigo_postal": "1900",
            },
        },
    )
    mocker.patch("core.models.Provincia.objects.get", return_value=SimpleNamespace(nombre="Buenos Aires"))
    r3 = view._consultar_renaper(SimpleNamespace(user=_User(superuser=True)), pk=1, legajo_id=1)
    body = json.loads(r3.content)
    assert body["success"] is True
    assert body["datos_renaper"]["provincia"] == "Buenos Aires"


def test_post_routes_to_save_or_consulta(mocker):
    view = module.ValidacionRenaperView()
    req_save = SimpleNamespace(POST={"validacion_estado": "1"})
    req_consulta = SimpleNamespace(POST={})

    save = mocker.patch.object(view, "_guardar_validacion_estado", return_value="save")
    consulta = mocker.patch.object(view, "_consultar_renaper", return_value="consulta")

    assert view.post.__wrapped__(view, req_save, 1, 2) == "save"
    assert save.called
    assert view.post.__wrapped__(view, req_consulta, 1, 2) == "consulta"
    assert consulta.called
