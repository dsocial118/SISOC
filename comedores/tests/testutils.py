import json
from pathlib import Path
from typing import Any
from comedores.models.comedor import Comedor
from comedores.models.relevamiento import (
    Relevamiento,
    TipoEspacio,
    TipoModalidadPrestacion,
    CantidadColaboradores,
)
from configuraciones.models import Provincia


class TestUtils:
    @staticmethod
    def cargar_mocked_data(nombre_archivo: str) -> dict:
        """
        Carga un archivo JSON con datos mockeados desde la carpeta 'mocked_data'.

        Args:
            nombre_archivo (str): Nombre del archivo JSON.
        """
        data_dir = Path(__file__).parent / "mocked_data"
        json_path = data_dir / nombre_archivo
        if not json_path.exists():
            raise FileNotFoundError(f"No se encontró el archivo: {json_path}")
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def crear_comedor_mock() -> Comedor:
        """
        Crea y retorna una instancia de Comedor para pruebas.
        """
        provincia, _ = Provincia.objects.get_or_create(nombre="Buenos Aires")
        comedor = Comedor.objects.create(
            nombre="Comedor de Testing",
            provincia=provincia,
            barrio="Centro",
            calle="Av. Siempre Viva",
            numero=123,
        )
        return comedor

    @staticmethod
    def crear_relevamiento_mock() -> Relevamiento:
        """
        Crea y retorna una instancia de Relevamiento para pruebas.
        """
        relevamiento = Relevamiento.objects.create(
            comedor=TestUtils.crear_comedor_mock(),
            estado="Pendiente",
            territorial_uid="1",
            territorial_nombre="Territorial de Testing",
        )
        relevamiento.save()
        return relevamiento

    @staticmethod
    def reemplazar_valores(obj: Any, replacements: dict[str, Any]) -> Any:
        """
        Reemplaza los valores de un objeto (dict, list, str) según el diccionario replacements.

        Args:
            obj (Any): Objeto a procesar.
            replacements (dict[str, Any]): Diccionario de reemplazos.
        """
        if isinstance(obj, dict):
            return {
                k: TestUtils.reemplazar_valores(v, replacements) for k, v in obj.items()
            }
        elif isinstance(obj, list):
            return [TestUtils.reemplazar_valores(item, replacements) for item in obj]
        elif isinstance(obj, str) and obj in replacements:
            return replacements[obj]
        return obj

    @staticmethod
    def crear_api_body_mock(nombre_archivo: str):
        """
        Crea un relevamiento y los datos iniciales completos a partir de un archivo JSON mockeado.

        Args:
            nombre_archivo (str): Nombre del archivo JSON con los datos mockeados.
        """
        mocked_data = TestUtils.cargar_mocked_data(nombre_archivo)

        initial_data = mocked_data.get("initial_data", {})

        return initial_data
