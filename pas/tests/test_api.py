from core.models import Municipio, Provincia
from pas.api import ResumenTitularPAS, obtener_resumen_titular
from pas.models import PasEstado, PasPersona


def test_obtener_resumen_titular_devuelve_dto_sin_modelos(db):
    estado = PasEstado.objects.create(nombre="Activo")
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    persona = PasPersona.objects.create(
        id_persona=501,
        apellidos="Pérez",
        nombres="Ana",
        dni=30111222,
        provincia=provincia,
        municipio=municipio,
        estado=estado,
    )

    resultado = obtener_resumen_titular(persona.pk)

    assert isinstance(resultado, ResumenTitularPAS)
    assert resultado.persona_id == persona.pk
    assert resultado.id_persona == 501
    assert resultado.estado == "Activo"


def test_obtener_resumen_titular_inexistente_devuelve_none(db):
    assert obtener_resumen_titular(999_999) is None
