from types import SimpleNamespace

from historial.services.historial_service.impl import HistorialService


def test_historial_documentos_usa_capacidad_publica_de_rendicion(mocker):
    mocker.patch(
        "historial.services.historial_service.impl.obtener_content_type_id_documento",
        return_value=17,
    )
    documentos = mocker.Mock()
    documentos.values_list.return_value.iterator.return_value = iter((2, 3))
    query = mocker.Mock()
    filtrar = mocker.patch(
        "historial.services.historial_service.impl.Historial.objects.filter",
        return_value=query,
    )

    HistorialService.get_historial_documentos_by_rendicion_cuentas_final(
        SimpleNamespace(documentos=documentos)
    )

    query.order_by.assert_called_once_with("-fecha")
    filtrar.assert_called_once_with(
        content_type_id=17,
        object_id__in=mocker.ANY,
    )
