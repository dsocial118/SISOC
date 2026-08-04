"""Import/export desde el Django admin (django-import-export).

Cubre el contrato que define `core/admin_import_export.py`: qué modelos aceptan
importación, cuáles solo exportan, y que la importación pase siempre por la
pantalla de preview antes de tocar la base.
"""

import pytest
from django.contrib import admin as django_admin
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import NoReverseMatch, reverse

from comedores.models import Programas
from core.models import Nacionalidad


def _indice_de_formato(model_admin, titulo, tipo="export"):
    formatos = (
        model_admin.get_export_formats()
        if tipo == "export"
        else model_admin.get_import_formats()
    )
    for indice, formato in enumerate(formatos):
        if formato().get_title() == titulo:
            return str(indice)
    raise AssertionError(f"Formato {titulo} no habilitado para {model_admin}")


@pytest.fixture(name="nacionalidad_admin")
def nacionalidad_admin_fixture():
    return django_admin.site._registry[Nacionalidad]


@pytest.mark.django_db
def test_formatos_limitados_a_xlsx_y_csv(nacionalidad_admin):
    titulos_import = {f().get_title() for f in nacionalidad_admin.get_import_formats()}
    titulos_export = {f().get_title() for f in nacionalidad_admin.get_export_formats()}

    assert titulos_import == {"xlsx", "csv"}
    assert titulos_export == {"xlsx", "csv"}


@pytest.mark.django_db
def test_export_csv_incluye_los_datos(auth_client, nacionalidad_admin):
    Nacionalidad.objects.create(nacionalidad="Argentina")

    response = auth_client.post(
        reverse("admin:core_nacionalidad_export"),
        {"format": _indice_de_formato(nacionalidad_admin, "csv")},
    )

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/csv"), response.context[
        "form"
    ].errors
    assert b"Argentina" in response.content


@pytest.mark.django_db
def test_export_xlsx_devuelve_un_archivo(auth_client, nacionalidad_admin):
    Nacionalidad.objects.create(nacionalidad="Argentina")

    response = auth_client.post(
        reverse("admin:core_nacionalidad_export"),
        {"format": _indice_de_formato(nacionalidad_admin, "xlsx")},
    )

    assert response.status_code == 200
    assert "spreadsheetml" in response["Content-Type"], response.context["form"].errors
    # Firma de un archivo xlsx (zip).
    assert response.content[:2] == b"PK"


@pytest.mark.django_db
def test_import_muestra_preview_sin_persistir_y_confirma(
    auth_client, nacionalidad_admin
):
    existente = Nacionalidad.objects.create(nacionalidad="Argentina")
    contenido = (
        "id,nacionalidad\n" f"{existente.pk},Argentina\n" ",Uruguaya\n"
    ).encode("utf-8")
    archivo = SimpleUploadedFile(
        "nacionalidades.csv", contenido, content_type="text/csv"
    )

    preview = auth_client.post(
        reverse("admin:core_nacionalidad_import"),
        {
            "import_file": archivo,
            "format": _indice_de_formato(nacionalidad_admin, "csv", tipo="import"),
        },
    )

    assert preview.status_code == 200
    assert "result" in preview.context
    # Preview: todavía no se escribió nada.
    assert Nacionalidad.objects.count() == 1

    confirm_form = preview.context["confirm_form"]
    confirmacion = auth_client.post(
        reverse("admin:core_nacionalidad_process_import"),
        confirm_form.initial,
    )

    assert confirmacion.status_code == 302
    assert Nacionalidad.objects.filter(nacionalidad="Uruguaya").exists()
    assert Nacionalidad.objects.count() == 2


@pytest.mark.django_db
def test_changelist_muestra_los_botones(auth_client):
    response = auth_client.get(reverse("admin:core_nacionalidad_changelist"))

    assert response.status_code == 200
    html = response.content.decode()
    assert reverse("admin:core_nacionalidad_import") in html
    assert reverse("admin:core_nacionalidad_export") in html


@pytest.mark.django_db
def test_modelo_export_only_no_expone_import(auth_client):
    programas_admin = django_admin.site._registry[Programas]
    assert not hasattr(programas_admin, "import_action")

    assert reverse("admin:comedores_programas_export")
    with pytest.raises(NoReverseMatch):
        reverse("admin:comedores_programas_import")


@pytest.mark.django_db
def test_export_only_sigue_exportando(auth_client):
    programas_admin = django_admin.site._registry[Programas]
    Programas.objects.create(nombre="Programa de prueba")

    response = auth_client.post(
        reverse("admin:comedores_programas_export"),
        {"format": _indice_de_formato(programas_admin, "csv")},
    )

    assert response.status_code == 200
    assert b"Programa de prueba" in response.content, response.context["form"].errors
