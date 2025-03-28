import sys
import os
import pytest
from comedores.services.clasificacion_comedor_service import ClasificacionComedorService
from comedores.services.test.crear_test_relevamiento import crear_test_relevamiento

@pytest.mark.django_db


def test_get_puntuacion_total():
    # Preparacion: Crear un relevamiento en la BD de prueba
    relevamiento = crear_test_relevamiento()

    # Ejecución: Llamar al método que queremos probar
    resultado = ClasificacionComedorService.get_puntuacion_total(relevamiento)

    # Verificación: Verificar que el resultado es el esperado
    assert resultado == 48

