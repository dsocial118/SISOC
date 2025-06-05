import pytest
from comedores.serializers.relevamiento_serializer import RelevamientoSerializer

from comedores.tests.testutils import TestUtils


@pytest.mark.django_db
def test_clean_success():
    relevamiento = TestUtils.crear_relevamiento_mock()
    comedor = TestUtils.crear_comedor_mock()

    initial_data = TestUtils.crear_api_body_mock("test_clean_datos_completos.json")
    initial_data["comedor"] = comedor.id

    serializer = RelevamientoSerializer(
        instance=relevamiento, data=initial_data, partial=True
    )

    if serializer.is_valid(raise_exception=True):
        serializer.save()

    assert (
        serializer.instance.fecha_visita.strftime("%-d/%-m/%Y %H:%M")
        == "5/3/2025 14:29"
    )
    assert serializer.instance.territorial_nombre == "Territorial de Testing"
    assert serializer.instance.imagenes == [
        "http://example.com/image1.jpg",
        "http://example.com/image2.jpg",
    ]


@pytest.mark.django_db
def test_clean_error_validation():
    relevamiento = TestUtils.crear_relevamiento_mock()

    initial_data = {
        "comedor": "{{comedor_id}}",
        "fecha_visita": "5/3/2025 14:29",
        "colaboradores": {
            "cantidad_colaboradores": "Esta opcion no es valida",
        },
    }

    serializer = RelevamientoSerializer(
        instance=relevamiento, data=initial_data, partial=True
    )

    assert not serializer.is_valid()

    error_msg = "CantidadColaboradores matching query does not exist."
    internal_errors = serializer.errors.get(
        "RelevamientoSerializer.to_internal_value()", []
    )
    assert any(error_msg in str(err) for err in internal_errors)
