import pytest
from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import reverse

from centrodeinfancia.models import (
    CentroDeInfancia,
    IntervencionCentroInfancia,
    ObservacionCentroInfancia,
)


@pytest.mark.django_db
@override_settings(
    CDI_ASISTENCIA_NOMINA_VISIBLE=False,
    CDI_FORMULARIOS_VISIBLE=False,
    CDI_INTERVENCIONES_VISIBLE=False,
)
def test_detalle_cdi_oculta_funcionalidades_suspendidas_y_mantiene_observaciones(
    client,
):
    user = User.objects.create_superuser(
        username="super-cdi-feature-visibility",
        email="feature-visibility@example.com",
        password="test1234",
    )
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Funcionalidades suspendidas")
    IntervencionCentroInfancia.objects.create(
        centro=centro,
        observaciones="Intervención que no debe mostrarse",
    )
    ObservacionCentroInfancia.objects.create(
        centro=centro,
        observador="Equipo territorial",
        observacion="Observación que debe mantenerse visible",
    )

    response = client.get(reverse("centrodeinfancia_detalle", kwargs={"pk": centro.pk}))

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Tomar asistencia" not in content
    assert "<span>Formularios</span>" not in content
    assert "Nueva Intervención" not in content
    assert "Intervención que no debe mostrarse" not in content
    assert "Observaciones" in content
    assert "Observación que debe mantenerse visible" in content


@pytest.mark.django_db
@override_settings(
    CDI_ASISTENCIA_NOMINA_VISIBLE=True,
    CDI_FORMULARIOS_VISIBLE=True,
    CDI_INTERVENCIONES_VISIBLE=True,
)
def test_detalle_cdi_restituye_las_funcionalidades_al_habilitar_los_flags(client):
    user = User.objects.create_superuser(
        username="super-cdi-feature-visible",
        email="feature-visible@example.com",
        password="test1234",
    )
    client.force_login(user)
    centro = CentroDeInfancia.objects.create(nombre="CDI Funcionalidades visibles")

    response = client.get(reverse("centrodeinfancia_detalle", kwargs={"pk": centro.pk}))

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert (
        reverse("centrodeinfancia_nomina_asistencia", kwargs={"pk": centro.pk})
        in content
    )
    assert "<span>Formularios</span>" in content
    assert "Nueva Intervención" in content
    assert "Intervenciones" in content
