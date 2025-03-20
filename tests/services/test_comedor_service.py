from configuraciones.models import Provincia
import pytest
from comedores.services.comedor_service import ComedorService
from comedores.models.comedor import Comedor

@pytest.mark.django_db
def test_get_comedor():
    # Preparacion: Crear un comedor en la BD de prueba
    provincia = Provincia.objects.create(nombre="Provincia Test")
    comedor = Comedor.objects.create(
        nombre="Comedor Test",
        provincia=provincia,
        barrio="Centro",
        calle="Av. Siempre Viva",
        numero=123
    )

    # Ejecución: Llamar al método que queremos probar
    resultado = ComedorService.get_comedor(comedor.id)

    # Verificación: Verificar que el resultado es el esperado
    assert resultado["id"] == comedor.id
    assert resultado["nombre"] == "Comedor Test"
    assert resultado["provincia"] == provincia.id
    assert resultado["barrio"] == "Centro"
    assert resultado["calle"] == "Av. Siempre Viva"
    assert resultado["numero"] == 123
