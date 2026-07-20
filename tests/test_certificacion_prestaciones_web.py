from datetime import date

import pytest
from django.core.files.base import ContentFile
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
