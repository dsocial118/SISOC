import pytest
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from comedores.models import Comedor
from comedores.services.comedor_service import ComedorService


@pytest.mark.django_db
def test_borrar_foto_legajo_elimina_archivo_y_nullea_campo(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    comedor = Comedor.objects.create(nombre="Test")
    file_content = ContentFile(b"data", "legajo.jpg")
    comedor.foto_legajo.save("legajo.jpg", file_content)
    file_name = comedor.foto_legajo.name

    assert default_storage.exists(file_name)

    ComedorService.borrar_foto_legajo({"foto_legajo_borrar": "1"}, comedor)

    assert not default_storage.exists(file_name)
    comedor.refresh_from_db()
    assert comedor.foto_legajo is None
