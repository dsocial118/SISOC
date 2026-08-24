from types import SimpleNamespace

from comedores import pwa_capabilities


def test_es_comedor_alimentar_comunidad_resuelve_el_programa(mocker):
    comedor = SimpleNamespace(programa=SimpleNamespace(nombre="Alimentar Comunidad"))
    mocker.patch(
        "comedores.pwa_capabilities.Comedor.objects.select_related",
        return_value=SimpleNamespace(
            filter=lambda **_kwargs: SimpleNamespace(first=lambda: comedor)
        ),
    )
    mocker.patch(
        "comedores.pwa_capabilities.is_alimentar_comunidad_program",
        return_value=True,
    )

    assert pwa_capabilities.es_comedor_alimentar_comunidad(10) is True
