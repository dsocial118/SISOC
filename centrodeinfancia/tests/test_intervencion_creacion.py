import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from centrodeinfancia.models import CentroDeInfancia, IntervencionCentroInfancia
from intervenciones.models.intervenciones import TipoContacto, TipoDestinatario, TipoIntervencion


@pytest.mark.django_db
def test_intervencion_create_guardar_usuario_creador(client):
    user = User.objects.create_superuser(
        username="super-intervencion-creador",
        email="super-intervencion-creador@example.com",
        password="test1234",
    )
    client.force_login(user)

    centro = CentroDeInfancia.objects.create(nombre="CDI Test Creador")
    tipo_intervencion = TipoIntervencion.objects.create(
        nombre="Seguimiento",
        programa="cdi",
    )
    TipoDestinatario.objects.create(nombre="Centro")
    forma_contacto = TipoContacto.objects.create(nombre="Presencial")

    response = client.post(
        reverse("centrodeinfancia_intervencion_crear", kwargs={"pk": centro.pk}),
        data={
            "tipo_intervencion": str(tipo_intervencion.pk),
            "subintervencion": "",
            "fecha": "2026-01-15",
            "forma_contacto": str(forma_contacto.pk),
            "observaciones": "Intervencion de prueba",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("centrodeinfancia_detalle", kwargs={"pk": centro.pk})

    intervencion = IntervencionCentroInfancia.objects.get(centro=centro)
    assert intervencion.creado_por == user
