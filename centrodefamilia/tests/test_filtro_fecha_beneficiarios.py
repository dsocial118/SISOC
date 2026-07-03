import json
from datetime import date, timedelta

import pytest
from django.contrib.auth.models import Permission, User
from django.urls import reverse
from django.utils import timezone

from centrodefamilia.models import Beneficiario, BeneficiarioResponsable, Responsable


def _payload(op, fecha):
    return json.dumps(
        {
            "logic": "AND",
            "items": [
                {
                    "field": "fecha_creado",
                    "op": op,
                    "value": fecha.strftime("%Y-%m-%d"),
                }
            ],
        }
    )


@pytest.fixture
def escenario(db):
    responsable = Responsable.objects.create(
        cuil=20285551113,
        dni=28555111,
        apellido="Gonzalez",
        nombre="Marta",
        genero="F",
        fecha_nacimiento=date(1980, 5, 12),
        vinculo_parental="Padre/Madre",
        calle="Av. Siempreviva",
    )
    beneficiario = Beneficiario.objects.create(
        cuil=20451112223,
        dni=45111222,
        apellido="Gonzalez",
        nombre="Sofia",
        genero="F",
        fecha_nacimiento=date(2012, 3, 4),
        domicilio="Av. Siempreviva 742",
        calle="Av. Siempreviva",
        maximo_nivel_educativo="Primario incompleto",
        responsable=responsable,
    )
    BeneficiarioResponsable.objects.create(
        beneficiario=beneficiario,
        responsable=responsable,
        vinculo_parental="Padre/Madre",
    )
    user = User.objects.create_user(username="admin-filtros", password="x")
    user.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="centrodefamilia", codename="view_centro"
        )
    )
    return user


@pytest.mark.django_db
@pytest.mark.parametrize("url_name", ["beneficiarios_list", "responsables_list"])
def test_filtro_fecha_desde_hasta_inclusivo(client, escenario, url_name):
    """Desde (gte) y Hasta (lte) incluyen los registros cargados ese mismo día."""
    client.force_login(escenario)
    url = reverse(url_name)
    hoy = timezone.localdate()
    manana = hoy + timedelta(days=1)

    desde_hoy = client.get(url, {"filters": _payload("gte", hoy)})
    desde_manana = client.get(url, {"filters": _payload("gte", manana)})
    hasta_hoy = client.get(url, {"filters": _payload("lte", hoy)})

    assert desde_hoy.status_code == 200
    assert "Gonzalez" in desde_hoy.content.decode()
    assert "Gonzalez" not in desde_manana.content.decode()
    assert "Gonzalez" in hasta_hoy.content.decode()
