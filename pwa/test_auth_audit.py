from pwa import auth_audit


def test_registrar_auditoria_auth_pwa_conecta_el_persistidor(mocker):
    registrar = mocker.patch("pwa.auth_audit.registrar_auditoria_auth")

    auth_audit.registrar_auditoria_auth_pwa()

    registrar.assert_called_once_with(auth_audit.registrar_evento_auth)
