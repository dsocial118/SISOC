import os
import json
from datetime import datetime
import pytest
from comedores.services.clasificacion_comedor_service import ClasificacionComedorService
from tests.test_clasificacion.crear_test_relevamiento import crear_test_relevamiento


def normalize_json(data):
    """
    Recorre recursivamente un diccionario o lista y reemplaza:
    - "N" por False
    - "Y" por True
    """
    if isinstance(data, dict):
        return {key: normalize_json(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [normalize_json(item) for item in data]
    elif data == "N":
        return False
    elif data == "Y":
        return True
    return data


@pytest.mark.django_db
def test_get_puntuacion_total_0():
    # Preparacion: Crear un relevamiento en la BD de prueba
    json_file_path = os.path.join(
        os.path.dirname(__file__), "json_relevamiento_puntuacion_0.json"
    )
    with open(json_file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Normalizar los valores del JSON
    data = normalize_json(data)

    fecha_visita = datetime.strptime(data["fecha_visita"], "%d/%m/%Y %H:%M").strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    # Extraer variables del JSON
    sisoc_id = data["sisoc_id"]
    gestionar_uid = data["gestionar_uid"]
    relevador = data["relevador"]
    estado = data["estado"]
    responsable_es_referente = data["responsable_es_referente"]
    responsable = data["responsable"]
    territorial = data["territorial"]
    funcionamiento = data["funcionamiento"]
    espacio = data["espacio"]
    colaboradores = data["colaboradores"]
    recursos = data["recursos"]
    compras = data["compras"]
    prestacion = data["prestacion"]
    observacion = data["observacion"]
    doc_pdf = data["docPDF"]
    anexo = data["anexo"]
    excepcion = data["excepcion"]
    punto_entregas = data["punto_entregas"]
    imagenes = data["imagenes"]
    suma_prueba = 0

    relevamiento = crear_test_relevamiento(
        sisoc_id=sisoc_id,
        gestionar_uid=gestionar_uid,
        relevador=relevador,
        estado=estado,
        fecha_visita=fecha_visita,
        responsable_es_referente=responsable_es_referente,
        responsable=responsable,
        territorial=territorial,
        funcionamiento=funcionamiento,
        espacio=espacio,
        colaboradores_json=colaboradores,
        recursos=recursos,
        compras_jxon=compras,
        prestacion=prestacion,
        observacion=observacion,
        doc_pdf=doc_pdf,
        anexo=anexo,
        excepcion=excepcion,
        punto_entregas=punto_entregas,
        imagenes_json=imagenes,
    )

    # Ejecución: Llamar al método que queremos probar
    resultado = ClasificacionComedorService.get_puntuacion_total(relevamiento)

    # Verificación: Verificar que el resultado es el esperado
    assert resultado == suma_prueba
