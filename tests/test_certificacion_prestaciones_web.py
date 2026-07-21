from datetime import date
from types import SimpleNamespace

import pytest
from django.core.files.base import ContentFile
from django.urls import reverse

from comedores.models import Comedor, PrestacionAlimentariaConformidad
from comedores.views.comedor import CertificacionesPrestacionesHistorialView


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
def test_historial_certificaciones_lista_todos_los_pdf(mocker, rf):
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
    request = rf.get("/certificaciones/")
    request.user = SimpleNamespace()
    mocker.patch(
        "comedores.views.comedor.ComedorService.get_comedor_detail_object",
        return_value=comedor,
    )
    view = CertificacionesPrestacionesHistorialView()
    view.request = request
    view.kwargs = {"pk": comedor.id}
    view.comedor = comedor

    certificaciones = list(view.get_queryset())

    assert len(certificaciones) == 7
    assert certificaciones[0].periodo == date(2035, 7, 1)
    assert all(certificacion.certificacion_pdf for certificacion in certificaciones)


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
