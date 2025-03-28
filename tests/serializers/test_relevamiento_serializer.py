from datetime import datetime, timezone
import pytest
from unittest.mock import patch
from comedores.models.relevamiento import Relevamiento, FuncionamientoPrestacion, Espacio, TipoEspacio, Colaboradores, FuenteRecursos, FuenteCompras, Anexo, PuntoEntregas, Prestacion, Excepcion
from comedores.serializers.relevamiento_serializer import RelevamientoSerializer
from comedores.models.comedor import Comedor, TipoDeComedor
from comedores.services.comedor_service import ComedorService
from configuraciones.models import Provincia




@pytest.mark.django_db
def test_clean_relevamiento_serializer():
    
    # Preparación: Crear un comedor y un relevamiento en la BD de prueba
    provincia = Provincia.objects.create(nombre="Provincia Test")
    comedor = Comedor.objects.create(
        nombre="Comedor Test",
        provincia=provincia,
        barrio="Centro",
        calle="Av. Siempre Viva",
        numero=123,
    )

    # Crear objetos para cada relación
    funcionamiento = FuncionamientoPrestacion.objects.create(
    )

    tipo_espacio = TipoEspacio.objects.create(nombre="Espacio Propio")
    espacio = Espacio.objects.create(tipo_espacio_fisico=tipo_espacio)

    colaboradores = Colaboradores.objects.create(
        cantidad_colaboradores=None,
        colaboradores_capacitados_alimentos=True,
    )

    recursos = FuenteRecursos.objects.create(
        recibe_donaciones_particulares=True,
    )

    compras = FuenteCompras.objects.create(
        almacen_cercano=True,
    )

    anexo = Anexo.objects.create(
        comedor_merendero=True,
    )

    punto_entregas = PuntoEntregas.objects.create(
        existe_punto_entregas=True,
    )

    prestacion = Prestacion.objects.create(
        lunes_desayuno_actual=10,
    )

    excepcion = Excepcion.objects.create(
        descripcion="Excepción Test",
    )
    

    relevamiento = Relevamiento.objects.create(
        comedor=comedor,
        estado="Pendiente",
        territorial_uid="1",
        territorial_nombre="Territorial Test",
    )

    # Datos iniciales para el serializer
    initial_data = {
        "comedor": comedor.id,
        "fecha_visita": "5/3/2025 14:29",
        "territorial": {"nombre": "Territorial Test", "gestionar_uid": "12345"},
        "funcionamiento": funcionamiento.id,
        "espacio": espacio.id,
        "colaboradores": colaboradores.id,
        "recursos": recursos.id,
        "compras": compras.id,
        "anexo": anexo.id,
        "punto_entregas": punto_entregas.id,
        "prestacion": prestacion.id,
        "excepcion": excepcion.id,
        "responsable_es_referente": "Y",
        "imagenes": "http://example.com/image1.jpg, http://example.com/image2.jpg",
    }

    # Crear el serializer con los datos iniciales y el relevamiento existente
    serializer = RelevamientoSerializer(instance=relevamiento, data=initial_data, partial=True).clean()
    if serializer.is_valid(raise_exception=True):
        serializer.save()

    

    # Verificar los valores procesados por el método clean
    assert serializer.instance["fecha_visita"] == "5/3/2025 14:29"
    assert serializer.instance["territorial_nombre"] == "Territorial Test"
    assert serializer.instance["territorial_uid"] == "12345"
    assert serializer.instance["responsable_es_referente"] is True
    assert serializer.instance["imagenes"] == [
        "http://example.com/image1.jpg",
        "http://example.com/image2.jpg",
    ]