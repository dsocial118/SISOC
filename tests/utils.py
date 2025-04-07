
from comedores.models.comedor import Comedor
from comedores.models.relevamiento import (
    Relevamiento,
    TipoEspacio,
    TipoModalidadPrestacion,
    CantidadColaboradores,
)
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