from types import SimpleNamespace

from ciudadanos import api


def test_prevalidar_ciudadano_existente_expone_datos_sin_modelo(mocker):
    ciudadano = SimpleNamespace(
        documento=12345678,
        nombre="Ana",
        apellido="Pérez",
        sexo="Femenino",
        fecha_nacimiento=None,
        edad=30,
        telefono="",
        pk=11,
    )
    mocker.patch("ciudadanos.api._buscar_ciudadano_verificado", return_value=ciudadano)

    resultado = api.prevalidar_ciudadano_renaper("12345678")

    assert resultado["success"] is True
    assert resultado["data"]["ciudadano_id"] == 11
    assert "ciudadano" not in resultado


def test_resolver_ciudadano_crea_y_expone_resumen(mocker):
    mocker.patch(
        "ciudadanos.api.prevalidar_ciudadano_renaper",
        return_value={
            "success": True,
            "pending_creation": True,
            "data": {"dni": 12345678},
            "datos_api": {"origen": "fake"},
        },
    )
    mocker.patch(
        "ciudadanos.api._datos_para_ciudadano",
        return_value=({"nombre": "Ana"}, None),
    )
    ciudadano = SimpleNamespace(
        documento=12345678,
        nombre="Ana",
        apellido="Pérez",
        sexo="Femenino",
        fecha_nacimiento=None,
        edad=30,
        telefono="",
        pk=12,
    )
    crear = mocker.patch(
        "ciudadanos.api.Ciudadano.objects.create", return_value=ciudadano
    )

    resultado = api.resolver_ciudadano_renaper("12345678")

    crear.assert_called_once_with(nombre="Ana")
    assert resultado["success"] is True
    assert resultado["data"]["ciudadano_id"] == 12


def test_resolver_ciudadano_rechaza_dni_invalido_de_renaper(mocker):
    mocker.patch(
        "ciudadanos.api.prevalidar_ciudadano_renaper",
        return_value={
            "success": True,
            "pending_creation": True,
            "data": {
                "dni": "no-es-un-dni",
                "nombre": "Ana",
                "apellido": "Pérez",
                "fecha_nacimiento": "2000-01-01",
            },
        },
    )

    resultado = api.resolver_ciudadano_renaper("12345678")

    assert resultado == {
        "success": False,
        "message": "RENAPER devolvió un DNI inválido.",
    }
