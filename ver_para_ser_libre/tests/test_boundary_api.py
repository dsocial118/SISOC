from ver_para_ser_libre import views


def test_resolver_ciudadano_registro_usa_la_fachada_de_ciudadanos(mocker):
    resultado = {"success": True, "ciudadano_id": 42}
    resolver = mocker.patch(
        "ver_para_ser_libre.views.resolver_ciudadano_renaper",
        return_value=resultado,
    )
    usuario = object()

    assert views._resolver_ciudadano_registro_vpsl(12345678, "F", usuario) == resultado
    resolver.assert_called_once_with(12345678, usuario=usuario, sexo="F")


def test_prevalidar_ciudadano_usa_la_fachada_de_ciudadanos(mocker):
    resultado = {"success": True, "data": {"dni": "12345678"}}
    prevalidar = mocker.patch(
        "ver_para_ser_libre.views.prevalidar_ciudadano_renaper",
        return_value=resultado,
    )

    assert views._prevalidar_ciudadano_registro_vpsl(12345678, "M") == resultado
    prevalidar.assert_called_once_with(12345678, sexo="M")
