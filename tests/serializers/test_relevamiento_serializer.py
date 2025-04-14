import pytest
from comedores.serializers.relevamiento_serializer import RelevamientoSerializer

from tests.utils import TestUtils


@pytest.mark.django_db
def test_clean_relevamiento_serializer_datos_completos():
    """
    Caso base: Datos completos y válidos.
    """
    datos, initial_data = TestUtils.crear_datos_completos(
        "test_clean_relevamiento_serializer_datos_completos.json"
    )

    serializer = RelevamientoSerializer(
        instance=datos["relevamiento"], data=initial_data, partial=True
    ).clean()
    if serializer.is_valid(raise_exception=True):
        serializer.save()

    assert (
        serializer.instance.fecha_visita.strftime("%-d/%-m/%Y %H:%M")
        == "5/3/2025 14:29"
    )
    assert serializer.instance.territorial_nombre == "Territorial Test"
    assert serializer.instance.imagenes == [
        "http://example.com/image1.jpg",
        "http://example.com/image2.jpg",
    ]


@pytest.mark.django_db
def test_clean_relevamiento_serializer_datos_incompletos():
    """
    Caso: Datos incompletos (faltan campos opcionales).
    """
    datos = TestUtils.crear_datos_relevamiento()

    initial_data = {
        "comedor": datos["comedor"].id,
        "fecha_visita": "5/3/2025 14:29",
        # Faltan campos opcionales como "territorial", "funcionamiento", etc.
    }

    serializer = RelevamientoSerializer(
        instance=datos["relevamiento"], data=initial_data, partial=True
    ).clean()
    if serializer.is_valid(raise_exception=True):
        serializer.save()

    assert (
        serializer.instance.fecha_visita.strftime("%-d/%-m/%Y %H:%M")
        == "5/3/2025 14:29"
    )


@pytest.mark.django_db
def test_clean_relevamiento_serializer_datos_minimos():
    """
    Caso: Datos mínimos necesarios.
    """
    datos = TestUtils.crear_datos_relevamiento()

    initial_data = {
        "comedor": datos["comedor"].id,
    }

    serializer = RelevamientoSerializer(
        instance=datos["relevamiento"], data=initial_data, partial=True
    ).clean()
    if serializer.is_valid(raise_exception=True):
        serializer.save()

    assert serializer.instance.comedor.id == datos["comedor"].id


@pytest.mark.django_db
def test_clean_relevamiento_serializer_datos_extra():
    """
    Caso: Datos adicionales no esperados.
    """
    datos = TestUtils.crear_datos_relevamiento()

    initial_data = {
        "comedor": datos["comedor"].id,
        "fecha_visita": "5/3/2025 14:29",
        "extra_field": "valor_no_esperado",  # Campo no definido en el serializer
    }

    serializer = RelevamientoSerializer(
        instance=datos["relevamiento"], data=initial_data, partial=True
    ).clean()
    if serializer.is_valid(raise_exception=True):
        serializer.save()

    assert (
        serializer.instance.fecha_visita.strftime("%-d/%-m/%Y %H:%M")
        == "5/3/2025 14:29"
    )


@pytest.mark.django_db
def test_clean_relevamiento_serializer_valores_limite():
    """
    Caso: Valores límite en los datos.
    """
    datos = TestUtils.crear_datos_relevamiento()

    initial_data = {
        "comedor": datos["comedor"].id,
        "fecha_visita": "1/1/1900 00:00",  # Fecha límite inferior
        "prestacion": {"lunes_desayuno_actual": 0},  # Valor límite inferior
    }

    serializer = RelevamientoSerializer(
        instance=datos["relevamiento"], data=initial_data, partial=True
    ).clean()
    if serializer.is_valid(raise_exception=True):
        serializer.save()

    assert (
        serializer.instance.fecha_visita.strftime("%-d/%-m/%Y %H:%M")
        == "1/1/1900 00:00"
    )
    assert serializer.instance.prestacion.lunes_desayuno_actual == 0


@pytest.mark.django_db
def test_clean_relevamiento_serializer_listas_vacias():
    """
    Caso: Listas vacías o nulas.
    """
    datos = TestUtils.crear_datos_relevamiento()

    initial_data = {
        "comedor": datos["comedor"].id,
        "imagenes": "",  # Lista vacía
    }

    serializer = RelevamientoSerializer(
        instance=datos["relevamiento"], data=initial_data, partial=True
    ).clean()
    if serializer.is_valid(raise_exception=True):
        serializer.save()

    assert serializer.instance.imagenes == []
