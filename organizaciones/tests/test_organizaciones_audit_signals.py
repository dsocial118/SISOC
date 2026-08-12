from organizaciones import audit_signals


class FirmanteFalso:
    organizacion = object()

    def __str__(self):
        return "Firmante de prueba"


def test_registrar_baja_firmante_no_duplica_eventos(mocker):
    registrar_evento = mocker.patch("organizaciones.audit_signals.registrar_evento")
    firmante = FirmanteFalso()

    audit_signals.registrar_baja_firmante(None, firmante)
    audit_signals.registrar_baja_firmante(None, firmante)

    registrar_evento.assert_called_once_with(
        firmante.organizacion,
        {"Firmante": ["Firmante de prueba", "Eliminado"]},
        audit_signals.ACTION_DELETE,
    )
