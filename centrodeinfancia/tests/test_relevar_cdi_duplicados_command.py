from io import StringIO

import pytest
from django.core.management import call_command

from centrodeinfancia.models import CentroDeInfancia
from core.models import Provincia


@pytest.mark.django_db
def test_comando_lista_solo_grupos_activos_completos_y_duplicados():
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    duplicado_1 = CentroDeInfancia.objects.create(
        nombre="CDI Uno",
        provincia=provincia,
        cuit_organizacion_gestiona="20-44535030-4",
        cuil_referente="20-44535030-4",
    )
    duplicado_2 = CentroDeInfancia.objects.create(
        nombre="CDI Dos",
        provincia=provincia,
        cuit_organizacion_gestiona="20445350304",
        cuil_referente="20445350304",
    )
    CentroDeInfancia.objects.create(
        nombre="CDI Sin CUIL",
        provincia=provincia,
        cuit_organizacion_gestiona="20445350304",
    )
    dado_de_baja = CentroDeInfancia.objects.create(
        nombre="CDI Dado de baja",
        provincia=provincia,
        cuit_organizacion_gestiona="20445350304",
        cuil_referente="20445350304",
    )
    dado_de_baja.delete()

    output = StringIO()
    call_command("relevar_cdi_duplicados", stdout=output)

    resultado = output.getvalue()
    assert "Grupos duplicados detectados: 1." in resultado
    assert f"{duplicado_1.pk} | CDI Uno" in resultado
    assert f"{duplicado_2.pk} | CDI Dos" in resultado
    assert "CDI Sin CUIL" not in resultado
    assert "CDI Dado de baja" not in resultado
    assert "*******0304" in resultado
