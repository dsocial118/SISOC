import pytest
from comedores.models.comedor import Comedor
from comedores.models.relevamiento import (
    Relevamiento,
    TipoEspacio,
    TipoModalidadPrestacion,
    CantidadColaboradores,
)
from comedores.serializers.relevamiento_serializer import RelevamientoSerializer
from configuraciones.models import Provincia


class RelevamientoTestHelper:
    """
    Clase auxiliar para crear datos de prueba relacionados con Relevamiento.
    """

    @staticmethod
    def crear_datos_relevamiento():
        """
        Crea y retorna las instancias necesarias para un relevamiento de prueba.
        """
        provincia = Provincia.objects.create(nombre="Provincia Test")
        comedor = Comedor.objects.create(
            nombre="Comedor Test",
            provincia=provincia,
            barrio="Centro",
            calle="Av. Siempre Viva",
            numero=123,
        )

        modalidad_prestacion = TipoModalidadPrestacion.objects.create(
            nombre="Servicio en el lugar"
        )
        cantidad_colaboradores = CantidadColaboradores.objects.create(nombre="1 a 3")
        tipo_espacio = TipoEspacio.objects.create(nombre="Espacio Propio")

        relevamiento = Relevamiento.objects.create(
            comedor=comedor,
            estado="Pendiente",
            territorial_uid="1",
            territorial_nombre="Territorial Test",
        )

        return {
            "provincia": provincia,
            "comedor": comedor,
            "modalidad_prestacion": modalidad_prestacion,
            "cantidad_colaboradores": cantidad_colaboradores,
            "tipo_espacio": tipo_espacio,
            "relevamiento": relevamiento,
        }


@pytest.mark.django_db
def test_clean_relevamiento_serializer_datos_completos():
    """
    Caso base: Datos completos y válidos.
    """
    datos = RelevamientoTestHelper.crear_datos_relevamiento()

    initial_data = {
        "comedor": datos["comedor"].id,
        "fecha_visita": "5/3/2025 14:29",
        "territorial": {"nombre": "Territorial Test", "gestionar_uid": "12345"},
        "funcionamiento": {
            "modalidad_prestacion": datos["modalidad_prestacion"].nombre,
            "servicio_por_turnos": False,
            "cantidad_turnos": 2,
        },
        "espacio": {"tipo_espacio_fisico": datos["tipo_espacio"].nombre},
        "colaboradores": {
            "cantidad_colaboradores": datos["cantidad_colaboradores"].nombre,
            "colaboradores_capacitados_alimentos": True,
        },
        "recursos": {"recibe_donaciones_particulares": True},
        "compras": {"almacen_cercano": True},
        "anexo": {"comedor_merendero": True},
        "punto_entregas": {"existe_punto_entregas": True},
        "prestacion": {"lunes_desayuno_actual": 10},
        "excepcion": {"descripcion": "Excepción Test"},
        "imagenes": "http://example.com/image1.jpg, http://example.com/image2.jpg",
    }

    serializer = RelevamientoSerializer(
        instance=datos["relevamiento"], data=initial_data, partial=True
    ).clean()
    if serializer.is_valid(raise_exception=True):
        serializer.save()

    assert serializer.instance.fecha_visita.strftime("%-d/%-m/%Y %H:%M") == "5/3/2025 14:29"
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
    datos = RelevamientoTestHelper.crear_datos_relevamiento()

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

    assert serializer.instance.fecha_visita.strftime("%-d/%-m/%Y %H:%M") == "5/3/2025 14:29"

@pytest.mark.django_db
def test_clean_relevamiento_serializer_datos_minimos():
    """
    Caso: Datos mínimos necesarios.
    """
    datos = RelevamientoTestHelper.crear_datos_relevamiento()

    initial_data = {
        "comedor": datos["comedor"].id,
    }

    serializer = RelevamientoSerializer(
        instance=datos["relevamiento"], data=initial_data, partial=True
    ).clean()
    if serializer.is_valid(raise_exception=True):
        serializer.save()

    assert serializer.instance.comedor.id == datos["comedor"].id