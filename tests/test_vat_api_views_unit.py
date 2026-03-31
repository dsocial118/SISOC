from types import SimpleNamespace

import pytest
from rest_framework.exceptions import ValidationError

from VAT.api_views import InscripcionViewSet


def test_inscripcion_viewset_perform_create_usa_inscripcion_service(mocker):
    view = InscripcionViewSet()
    view.request = SimpleNamespace(user=SimpleNamespace(is_authenticated=True))

    ciudadano = SimpleNamespace(id=1)
    comision = SimpleNamespace(id=2)
    programa = SimpleNamespace(id=3)
    inscripcion = SimpleNamespace(id=10)
    serializer = mocker.Mock()
    serializer.validated_data = {
        "ciudadano": ciudadano,
        "comision": comision,
        "programa": programa,
        "estado": "inscripta",
        "origen_canal": "api",
        "observaciones": "ok",
    }

    crear_mock = mocker.patch(
        "VAT.api_views.InscripcionService.crear_inscripcion", return_value=inscripcion
    )

    view.perform_create(serializer)

    crear_mock.assert_called_once_with(
        ciudadano=ciudadano,
        comision=comision,
        programa=programa,
        estado="inscripta",
        origen_canal="api",
        observaciones="ok",
        usuario=view.request.user,
    )
    assert serializer.instance is inscripcion


def test_inscripcion_viewset_perform_create_convierte_value_error_en_400(mocker):
    view = InscripcionViewSet()
    view.request = SimpleNamespace(user=None)

    serializer = mocker.Mock()
    serializer.validated_data = {
        "ciudadano": SimpleNamespace(id=1),
        "comision": SimpleNamespace(id=2),
    }

    mocker.patch(
        "VAT.api_views.InscripcionService.crear_inscripcion",
        side_effect=ValueError("Sin voucher"),
    )

    with pytest.raises(ValidationError) as exc_info:
        view.perform_create(serializer)

    assert exc_info.value.detail == {"error": ["Sin voucher"]}
