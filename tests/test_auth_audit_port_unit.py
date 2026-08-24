import pytest

from users import auth_audit


def test_registrar_evento_auth_requiere_un_persistidor(monkeypatch):
    monkeypatch.setattr(auth_audit, "_registrar_evento", None)

    with pytest.raises(RuntimeError, match="No hay un persistidor"):
        auth_audit.registrar_evento_auth(evento="login_ok")


def test_registrar_evento_auth_delega_en_el_persistidor_registrado(monkeypatch):
    eventos = []
    monkeypatch.setattr(auth_audit, "_registrar_evento", None)
    auth_audit.registrar_auditoria_auth(lambda **kwargs: eventos.append(kwargs))

    auth_audit.registrar_evento_auth(evento="login_ok", resultado="ok")

    assert eventos == [{"evento": "login_ok", "resultado": "ok"}]
