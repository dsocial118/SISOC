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


_PERM_TO_GROUP = {
    "auth.role_tecnicoceliaquia": "TecnicoCeliaquia",
    "auth.role_coordinadorceliaquia": "CoordinadorCeliaquia",
}


class _User:
    def __init__(self, auth=True, superuser=False, groups=None, user_id=10):
        self.is_authenticated = auth
        self.is_superuser = superuser
        self.groups = groups or _Groups()
        self.id = user_id

    def get_username(self):
        return "tester"

    def has_perm(self, perm, obj=None):
        if not self.is_authenticated:
            return False
        if self.is_superuser:
            return True
        group_name = _PERM_TO_GROUP.get(perm)
        if group_name:
            return self.groups.filter(group_name).exists()
        return False


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


def _crear_ciudadano_base(sexo="Masculino"):
    return SimpleNamespace(
        documento="20123456780",
        sexo=SimpleNamespace(sexo=sexo) if sexo else None,
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


@pytest.mark.parametrize(
    "value,length,expected",
    [("abc", 10, "abc"), ("a" * 8, 5, "aaaaa…"), (123, 5, 123)],
)
def test_helpers_truncate(value, length, expected):
    assert module._truncate(value, length) == expected


def test_helpers_build_log_data():
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
    mocker.patch(
        "celiaquia.views.validacion_renaper.get_object_or_404", return_value=legajo
    )

    invalid = view._guardar_validacion_estado(
        req, pk=1, legajo_id=2, validacion_estado="9"
    )
    assert json.loads(invalid.content)["success"] is False

    subsanar = view._guardar_validacion_estado(
        req, pk=1, legajo_id=2, validacion_estado="3"
    )
    assert json.loads(subsanar.content)["success"] is True
    assert legajo.revision_tecnico == "SUBSANAR"
    assert "subsanacion_motivo" in legajo.saved_fields

    mocker.patch(
        "celiaquia.views.validacion_renaper.get_object_or_404",
        side_effect=RuntimeError("boom"),
    )
    err = view._guardar_validacion_estado(req, pk=1, legajo_id=2, validacion_estado="1")
    assert err.status_code == 500


def test_consultar_renaper_guard_clauses(mocker):
    view = module.ValidacionRenaperView()
    tecnico = _User(groups=_Groups({"TecnicoCeliaquia"}))

    legajo_no_asig = _Legajo(
        ciudadano=SimpleNamespace(documento="12345678"), assigned=False
    )
    mocker.patch(
        "celiaquia.views.validacion_renaper.get_object_or_404",
        return_value=legajo_no_asig,
    )
    resp_forbidden = view._consultar_renaper(
        SimpleNamespace(user=tecnico), pk=1, legajo_id=1
    )
    assert resp_forbidden.status_code == 403

    legajo_sin_ciudadano = _Legajo(ciudadano=None, assigned=True)
    mocker.patch(
        "celiaquia.views.validacion_renaper.get_object_or_404",
        return_value=legajo_sin_ciudadano,
    )
    resp_no_cit = view._consultar_renaper(
        SimpleNamespace(user=_User(superuser=True)), pk=1, legajo_id=1
    )
    assert json.loads(resp_no_cit.content)["success"] is False

    legajo_bad_doc = _Legajo(
        ciudadano=SimpleNamespace(
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
        ),
        assigned=True,
    )
    mocker.patch(
        "celiaquia.views.validacion_renaper.get_object_or_404",
        return_value=legajo_bad_doc,
    )
    resp_bad_doc = view._consultar_renaper(
        SimpleNamespace(user=_User(superuser=True)), pk=1, legajo_id=1
    )
    assert json.loads(resp_bad_doc.content)["error"].startswith(
        "No se pudo extraer DNI válido"
    )


def test_consultar_renaper_fallecido_y_exito(mocker):
    view = module.ValidacionRenaperView()

    legajo_fall = _Legajo(ciudadano=_crear_ciudadano_base())
    mocker.patch(
        "celiaquia.views.validacion_renaper.get_object_or_404", return_value=legajo_fall
    )
    mocker.patch(
        "celiaquia.views.validacion_renaper.consultar_datos_renaper",
        return_value={
            "success": False,
            "fallecido": True,
            "error": "El ciudadano se encuentra fallecido.",
            "error_type": "fallecido",
            "raw_response": {"mensaf": "FALLECIDO"},
        },
    )
    info = mocker.patch.object(module.logger, "info")

    r1 = view._consultar_renaper(
        SimpleNamespace(user=_User(superuser=True)), pk=1, legajo_id=1
    )

    assert "fallecida" in json.loads(r1.content)["error"]
    info_messages = [call.args[0] for call in info.call_args_list]
    assert "renaper.validation.fallecido" in info_messages

    legajo_ok = _Legajo(ciudadano=_crear_ciudadano_base())
    mocker.patch(
        "celiaquia.views.validacion_renaper.get_object_or_404", return_value=legajo_ok
    )
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
    mocker.patch(
        "core.models.Provincia.objects.get",
        return_value=SimpleNamespace(nombre="Buenos Aires"),
    )

    r2 = view._consultar_renaper(
        SimpleNamespace(user=_User(superuser=True)), pk=1, legajo_id=1
    )
    body = json.loads(r2.content)
    assert body["success"] is True
    assert body["datos_renaper"]["provincia"] == "Buenos Aires"


def test_consultar_renaper_remote_error_muestra_mensaje_funcional(mocker):
    view = module.ValidacionRenaperView()
    legajo = _Legajo(ciudadano=_crear_ciudadano_base())
    mocker.patch(
        "celiaquia.views.validacion_renaper.get_object_or_404", return_value=legajo
    )
    mocker.patch(
        "celiaquia.views.validacion_renaper.consultar_datos_renaper",
        return_value={
            "success": False,
            "error": "temporarily unavailable",
            "error_type": "remote_error",
            "raw_response": {"message": "upstream down"},
        },
    )

    response = view._consultar_renaper(
        SimpleNamespace(user=_User(superuser=True)), pk=1, legajo_id=1
    )

    assert (
        json.loads(response.content)["error"]
        == module.RENAPER_REMOTE_UNAVAILABLE_MESSAGE
    )


def test_consultar_renaper_invalid_response_muestra_mensaje_y_log(mocker):
    mocker.patch.object(module.settings, "RENAPER_VALIDACION_MAX_RETRIES", 1)
    mocker.patch.object(module.settings, "RENAPER_VALIDACION_BACKOFF_SECONDS", 0)
    view = module.ValidacionRenaperView()
    legajo = _Legajo(ciudadano=_crear_ciudadano_base())
    mocker.patch(
        "celiaquia.views.validacion_renaper.get_object_or_404", return_value=legajo
    )
    mocker.patch(
        "celiaquia.views.validacion_renaper.consultar_datos_renaper",
        return_value={
            "success": False,
            "error": "payload invalido",
            "error_type": "invalid_response",
            "raw_response": {"broken": True},
        },
    )
    error = mocker.patch.object(module.logger, "error")

    response = view._consultar_renaper(
        SimpleNamespace(user=_User(superuser=True)), pk=1, legajo_id=1
    )
    body = json.loads(response.content)

    assert body["error"] == module.RENAPER_INVALID_RESPONSE_MESSAGE
    assert error.call_args[0][0] == "renaper.validation.invalid_response"
    log_data = error.call_args[1]["extra"]["data"]
    assert log_data["stage"] == "response"
    assert log_data["error_type"] == "invalid_response"
    assert log_data["retry_attempt"] == 1
    assert log_data["max_retries"] == 1
    assert '"broken": true' in log_data["raw_response_excerpt"]


def test_no_match_no_reintenta_ni_loguea_retry(mocker):
    mocker.patch.object(module.settings, "RENAPER_VALIDACION_MAX_RETRIES", 3)
    mocker.patch.object(module.settings, "RENAPER_VALIDACION_BACKOFF_SECONDS", 0.25)
    consultar = mocker.patch(
        "celiaquia.views.validacion_renaper.consultar_datos_renaper",
        return_value={
            "success": False,
            "error": "No se encontro coincidencia.",
            "error_type": "no_match",
            "raw_response": {"isSuccess": False},
        },
    )
    warning = mocker.patch.object(module.logger, "warning")
    sleep = mocker.patch("celiaquia.views.validacion_renaper.time.sleep")

    out = module._consultar_datos_renaper_con_reintentos("12345678", "M")

    assert out["error_type"] == "no_match"
    assert out["retry_attempt"] == 1
    assert out["max_retries"] == 3
    assert consultar.call_count == 1
    sleep.assert_not_called()
    assert not any(
        call.args[0] == "renaper.validation.retrying_remote_query"
        for call in warning.call_args_list
    )


def test_no_match_loguea_solo_no_match_y_mensaje_funcional(mocker):
    mocker.patch.object(module.settings, "RENAPER_VALIDACION_MAX_RETRIES", 1)
    mocker.patch.object(module.settings, "RENAPER_VALIDACION_BACKOFF_SECONDS", 0)
    view = module.ValidacionRenaperView()
    legajo = _Legajo(ciudadano=_crear_ciudadano_base())
    mocker.patch(
        "celiaquia.views.validacion_renaper.get_object_or_404", return_value=legajo
    )
    mocker.patch(
        "celiaquia.views.validacion_renaper.consultar_datos_renaper",
        return_value={
            "success": False,
            "error": "No se encontro coincidencia.",
            "error_type": "no_match",
            "raw_response": {"isSuccess": False, "detalle": "mismatch"},
        },
    )
    info = mocker.patch.object(module.logger, "info")
    warning = mocker.patch.object(module.logger, "warning")
    error = mocker.patch.object(module.logger, "error")

    response = view._consultar_renaper(
        SimpleNamespace(user=_User(superuser=True)), pk=1, legajo_id=1
    )
    body = json.loads(response.content)

    assert body["error"] == module.RENAPER_NO_MATCH_MESSAGE
    info_messages = [call.args[0] for call in info.call_args_list]
    assert "renaper.validation.no_match" in info_messages
    warning_messages = [call.args[0] for call in warning.call_args_list]
    assert "renaper.validation.no_match" not in warning_messages
    assert "renaper.validation.retrying_remote_query" not in warning_messages
    error_messages = [call.args[0] for call in error.call_args_list]
    assert "renaper.validation.response_error" not in error_messages
    no_match_logs = [
        call
        for call in info.call_args_list
        if call.args[0] == "renaper.validation.no_match"
    ]
    assert len(no_match_logs) == 1
    log_data = no_match_logs[0].kwargs["extra"]["data"]
    assert log_data["error_type"] == "no_match"
    assert log_data["retry_attempt"] == 1
    assert log_data["max_retries"] == 1
    assert '"detalle": "mismatch"' in log_data["raw_response_excerpt"]


def test_consultar_datos_renaper_con_reintentos_respeta_backoff_y_retry_log(mocker):
    mocker.patch.object(module.settings, "RENAPER_VALIDACION_MAX_RETRIES", 3)
    mocker.patch.object(module.settings, "RENAPER_VALIDACION_BACKOFF_SECONDS", 0.25)
    consultar = mocker.patch(
        "celiaquia.views.validacion_renaper.consultar_datos_renaper",
        side_effect=[
            {"success": False, "error": "timeout 1", "error_type": "timeout"},
            {"success": False, "error": "timeout 2", "error_type": "timeout"},
            {"success": True, "data": {"documento": "12345678"}},
        ],
    )
    warning = mocker.patch.object(module.logger, "warning")
    sleep = mocker.patch("celiaquia.views.validacion_renaper.time.sleep")

    out = module._consultar_datos_renaper_con_reintentos("12345678", "M")

    assert out["success"] is True
    assert out["retry_attempt"] == 3
    assert out["max_retries"] == 3
    assert consultar.call_count == 3
    assert sleep.call_count == 2
    assert sleep.call_args_list[0].args == (0.25,)
    assert sleep.call_args_list[1].args == (0.5,)
    retry_logs = [
        call
        for call in warning.call_args_list
        if call.args[0] == "renaper.validation.retrying_remote_query"
    ]
    assert len(retry_logs) == 2
    assert retry_logs[0].kwargs["extra"]["data"]["error_type"] == "timeout"


def test_consultar_datos_renaper_con_reintentos_defaults_invalidos(mocker):
    mocker.patch.object(module.settings, "RENAPER_VALIDACION_MAX_RETRIES", "abc")
    mocker.patch.object(module.settings, "RENAPER_VALIDACION_BACKOFF_SECONDS", "x")
    consultar = mocker.patch(
        "celiaquia.views.validacion_renaper.consultar_datos_renaper",
        return_value={"success": False, "error": "fail", "error_type": "remote_error"},
    )
    sleep = mocker.patch("celiaquia.views.validacion_renaper.time.sleep")

    out = module._consultar_datos_renaper_con_reintentos("12345678", "F")

    assert out["success"] is False
    assert out["retry_attempt"] == 1
    assert consultar.call_count == 1
    sleep.assert_not_called()


def test_formatear_datos_renaper_usa_provincia_api_cuando_no_hay_pk():
    datos = {
        "dni": 12345678,
        "nombre": "ANA",
        "apellido": "PEREZ",
        "fecha_nacimiento": "2000-01-02",
        "calle": "MITRE",
        "altura": 10,
        "piso_vivienda": "1A",
        "localidad_api": "LA PLATA",
        "provincia_api": "buenos aires",
        "codigo_postal": 1900,
    }

    out = module._formatear_datos_renaper(datos, "F", documento_consulta="12345678")

    assert out["documento"] == "12345678"
    assert out["provincia"] == "Buenos Aires"
    assert out["ciudad"] == "La Plata"
    assert out["piso_departamento"] == "1A"


def test_build_datos_provincia_usa_localidad_como_ciudad():
    ciudadano = SimpleNamespace(
        nombre="ana",
        apellido="perez",
        fecha_nacimiento=None,
        sexo=SimpleNamespace(sexo="Femenino"),
        calle="mitre",
        altura=10,
        piso_departamento="1a",
        localidad=SimpleNamespace(nombre="saenz peña"),
        ciudad="",
        provincia=SimpleNamespace(nombre="Chaco"),
        codigo_postal="3700",
    )

    out = module._build_datos_provincia(ciudadano, "12345678")

    assert out["ciudad"] == "Saenz Peña"
    assert out["provincia"] == "Chaco"


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


def test_consultar_renaper_sin_sexo_reintenta_y_reutiliza_respuesta(mocker):
    view = module.ValidacionRenaperView()
    ciudadano = _crear_ciudadano_base(sexo=None)
    ciudadano.documento = "12345678"
    legajo = _Legajo(ciudadano=ciudadano, assigned=True)
    mocker.patch(
        "celiaquia.views.validacion_renaper.get_object_or_404",
        return_value=legajo,
    )
    consultar = mocker.patch(
        "celiaquia.views.validacion_renaper.consultar_datos_renaper",
        side_effect=[
            {"success": False, "error": "mismatch", "error_type": "no_match"},
            {
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
                    "provincia": None,
                    "codigo_postal": "1900",
                },
            },
        ],
    )

    resp = view._consultar_renaper(
        SimpleNamespace(user=_User(superuser=True)), pk=1, legajo_id=1
    )
    body = json.loads(resp.content)

    assert body["success"] is True
    assert body["datos_renaper"]["sexo"] == "Femenino"
    assert consultar.call_count == 2
    assert consultar.call_args_list[0].args == ("12345678", "M")
    assert consultar.call_args_list[1].args == ("12345678", "F")
