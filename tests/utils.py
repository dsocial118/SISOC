import json
from pathlib import Path
from comedores.models.comedor import Comedor
from comedores.models.relevamiento import (
    Relevamiento,
    TipoEspacio,
    TipoModalidadPrestacion,
    CantidadColaboradores,
)
from configuraciones.models import Provincia


class TestUtils:
    """
    Clase auxiliar para crear datos de prueba relacionados con Relevamiento.
    """

    @staticmethod
    def cargar_initial_data(json_file, datos):
        # Obtener la ruta al archivo JSON
        data_dir = Path(__file__).parent / "mocked_data"
        json_path = data_dir / json_file

        # Cargar el JSON
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Reemplazar placeholders con valores reales
        initial_data = data["initial_data"]

        # Reemplazar valores dinámicos
        replacements = {
            "{{comedor_id}}": str(datos["comedor"].id),
            "{{modalidad_prestacion_nombre}}": datos["modalidad_prestacion"].nombre,
            "{{tipo_espacio_nombre}}": datos["tipo_espacio"].nombre,
            "{{cantidad_colaboradores_nombre}}": datos["cantidad_colaboradores"].nombre,
        }

        # Función para reemplazar en toda la estructura
        def replace_values(obj):
            if isinstance(obj, dict):
                return {k: replace_values(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_values(item) for item in obj]
            elif isinstance(obj, str) and obj in replacements:
                return replacements[obj]
            return obj

        return replace_values(initial_data)

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

    @staticmethod
    def crear_datos_completos(json_file):
        datos = TestUtils.crear_datos_relevamiento()
        initial_data = TestUtils.cargar_initial_data(json_file, datos)
        return datos, initial_data
