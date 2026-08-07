from intervenciones import fixture_post_load


def test_sincronizar_catalogo_intervenciones_conserva_el_mensaje_operativo(mocker):
    mocker.patch(
        "intervenciones.fixture_post_load.sync_catalogo_intervenciones",
        return_value={
            "tipos_sincronizados": 1,
            "subtipos_sincronizados": 2,
            "subtipos_vacios_eliminados": 3,
        },
    )

    assert fixture_post_load.sincronizar_catalogo_intervenciones() == (
        "✅ Catálogo de intervenciones sincronizado: "
        "tipos=1, subtipos=2, subtipos_vacios_eliminados=3"
    )


def test_registrar_fixture_post_load_handler_registra_el_callback(mocker):
    registrar = mocker.patch("intervenciones.fixture_post_load.registrar_handler")

    fixture_post_load.registrar_fixture_post_load_handler()

    registrar.assert_called_once_with(
        "intervenciones.catalogo",
        fixture_post_load.sincronizar_catalogo_intervenciones,
    )
