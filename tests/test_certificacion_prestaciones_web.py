from datetime import date

import pytest
from django.core.files.base import ContentFile
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from comedores.models import Comedor, PrestacionAlimentariaConformidad


@pytest.mark.django_db
def test_descarga_certificacion_web_requiere_autenticacion(client):
    comedor = Comedor.objects.create(nombre="Espacio certificado")
    certificacion = PrestacionAlimentariaConformidad.objects.create(
        comedor=comedor,
        periodo=date(2035, 1, 1),
        conforme=True,
    )
    certificacion.certificacion_pdf.save("certificacion.pdf", ContentFile(b"%PDF"))

    response = client.get(
        reverse(
            "descargar_certificacion_prestaciones_web",
            args=[comedor.id, certificacion.id],
        )
    )

    assert response.status_code in (302, 403)


@pytest.mark.django_db
def test_historial_certificaciones_lista_todos_los_pdf(client, django_user_model):
    user = django_user_model.objects.create_superuser(
        username="historial_certificaciones_admin",
        password="testpass",
        email="historial-certificaciones@example.com",
    )
    client.force_login(user)
    comedor = Comedor.objects.create(nombre="Espacio con historial")
    for mes in range(1, 8):
        certificacion = PrestacionAlimentariaConformidad.objects.create(
            comedor=comedor,
            periodo=date(2035, mes, 1),
            conforme=True,
        )
        certificacion.certificacion_pdf.save(
            f"certificacion-{mes}.pdf", ContentFile(b"%PDF")
        )
    PrestacionAlimentariaConformidad.objects.create(
        comedor=comedor,
        periodo=date(2034, 12, 1),
        conforme=True,
    )
    response = client.get(
        reverse("certificaciones_prestaciones_historial", kwargs={"pk": comedor.id})
    )

    assert response.status_code == 200
    content = response.content.decode()
    assert "07/2035" in content
    assert "01/2035" in content
    assert "12/2034" not in content


@pytest.mark.django_db
def test_historial_certificaciones_no_precarga_el_legajo_completo(
    client, django_user_model
):
    user = django_user_model.objects.create_superuser(
        username="historial_liviano_admin",
        password="testpass",
        email="historial-liviano@example.com",
    )
    client.force_login(user)
    comedor = Comedor.objects.create(nombre="Espacio con historial liviano")

    with CaptureQueriesContext(connection) as queries:
        response = client.get(
            reverse("certificaciones_prestaciones_historial", kwargs={"pk": comedor.id})
        )

    assert response.status_code == 200
    assert len(queries) <= 6


@pytest.mark.django_db
def test_legajo_muestra_seis_certificaciones_antes_de_colaboradores(
    client, django_user_model, monkeypatch
):
    user = django_user_model.objects.create_superuser(
        username="certificaciones_admin",
        password="testpass",
        email="certificaciones@example.com",
    )
    client.force_login(user)
    comedor = Comedor.objects.create(nombre="Espacio con seis certificaciones")
    monkeypatch.setattr(
        "comedores.services.comedor_service.ComedorService.get_presupuestos",
        lambda *args, **kwargs: (10, 1, 2, 3, 4, 5),
    )
    for mes in range(1, 8):
        certificacion = PrestacionAlimentariaConformidad.objects.create(
            comedor=comedor,
            periodo=date(2035, mes, 1),
            conforme=True,
        )
        certificacion.certificacion_pdf.save(
            f"certificacion-{mes}.pdf", ContentFile(b"%PDF")
        )

    response = client.get(reverse("comedor_detalle", kwargs={"pk": comedor.id}))

    assert response.status_code == 200
    content = response.content.decode()
    assert content.index("Certificaciones Mensuales de Prestaciones") < content.index(
        "Colaboradores del espacio"
    )
    assert "07/2035" in content
    assert "02/2035" in content
    assert "01/2035" not in content
    assert "Ver historial completo" in content

    historial = client.get(
        reverse("certificaciones_prestaciones_historial", kwargs={"pk": comedor.id})
    )
    assert historial.status_code == 200
    historial_content = historial.content.decode()
    assert "07/2035" in historial_content
    assert "01/2035" in historial_content
