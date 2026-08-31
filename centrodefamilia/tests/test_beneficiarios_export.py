import codecs
import csv
import json
from datetime import date
from io import StringIO

import pytest
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from centrodefamilia.models import Beneficiario, Responsable
from core.models import Localidad, Municipio, Provincia


def _payload(field, value, op="eq"):
    return json.dumps(
        {"logic": "AND", "items": [{"field": field, "op": op, "value": value}]}
    )


def _grant_export_role(user):
    content_type = ContentType.objects.get_for_model(Group)
    permission, _ = Permission.objects.get_or_create(
        content_type=content_type,
        codename="role_exportar_a_csv",
        defaults={"name": "Exportar a csv"},
    )
    user.user_permissions.add(permission)
    return User.objects.get(pk=user.pk)


def _grant_cdf_sse_role(user):
    content_type = ContentType.objects.get_for_model(Group)
    permission, _ = Permission.objects.get_or_create(
        content_type=content_type,
        codename="role_cdf_sse",
        defaults={"name": "CDF SSE"},
    )
    user.user_permissions.add(permission)
    return User.objects.get(pk=user.pk)


def _crear_usuario_listado(username):
    user = User.objects.create_user(username=username, password="x")
    user.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="centrodefamilia", codename="view_centro"
        )
    )
    return user


@pytest.fixture
def usuario_con_permisos(db):
    return _grant_export_role(_crear_usuario_listado("cdf-export"))


@pytest.fixture
def usuario_cdf_sse(db):
    """Rol CDF SSE: exporta preinscriptos sin el rol transversal de CSV."""
    return _grant_cdf_sse_role(_crear_usuario_listado("cdf-sse"))


@pytest.fixture
def beneficiarios(db):
    buenos_aires = Provincia.objects.create(nombre="Buenos Aires")
    cordoba = Provincia.objects.create(nombre="Cordoba")

    responsable_1 = Responsable.objects.create(
        cuil=20285551113,
        dni=28555111,
        apellido="Gonzalez",
        nombre="Marta",
        genero="F",
        fecha_nacimiento=date(1980, 5, 12),
        vinculo_parental="Padre/Madre",
        calle="Av. Siempreviva",
    )
    beneficiario_ba = Beneficiario.objects.create(
        cuil=20451112223,
        dni=45111222,
        apellido="Perez",
        nombre="Sofia",
        genero="F",
        fecha_nacimiento=date(2012, 3, 4),
        domicilio="Av. Siempreviva 742",
        calle="Av. Siempreviva",
        maximo_nivel_educativo="Primario incompleto",
        responsable=responsable_1,
        provincia=buenos_aires,
    )

    responsable_2 = Responsable.objects.create(
        cuil=20285551114,
        dni=28555112,
        apellido="Diaz",
        nombre="Laura",
        genero="F",
        fecha_nacimiento=date(1982, 6, 20),
        vinculo_parental="Padre/Madre",
        calle="Calle Falsa",
    )
    beneficiario_cba = Beneficiario.objects.create(
        cuil=20451112224,
        dni=45111223,
        apellido="Lopez",
        nombre="Juan",
        genero="M",
        fecha_nacimiento=date(2013, 7, 10),
        domicilio="Calle Falsa 123",
        calle="Calle Falsa",
        maximo_nivel_educativo="Primario incompleto",
        responsable=responsable_2,
        provincia=cordoba,
    )

    return beneficiario_ba, beneficiario_cba


@pytest.mark.django_db
def test_export_sin_filtro_incluye_todos_y_nombra_archivo_todos(
    client, usuario_con_permisos, beneficiarios
):
    client.force_login(usuario_con_permisos)
    response = client.get(reverse("beneficiarios_export"))

    assert response.status_code == 200
    assert (
        response["Content-Disposition"]
        == 'attachment; filename="beneficiarios_todos.csv"'
    )

    raw_content = b"".join(response.streaming_content)
    assert raw_content.startswith(codecs.BOM_UTF8)
    assert not raw_content[len(codecs.BOM_UTF8) :].startswith(codecs.BOM_UTF8)
    content = raw_content.decode("utf-8-sig")
    reader = csv.DictReader(StringIO(content), delimiter=";")
    rows = list(reader)

    assert {row["CUIL"] for row in rows} == {"20451112223", "20451112224"}


@pytest.mark.django_db
def test_export_respeta_filtro_de_provincia_y_nombra_archivo_con_provincia(
    client, usuario_con_permisos, beneficiarios
):
    client.force_login(usuario_con_permisos)
    response = client.get(
        reverse("beneficiarios_export"),
        {"filters": _payload("provincia", "Buenos Aires")},
    )

    assert response.status_code == 200
    assert response["Content-Disposition"] == (
        'attachment; filename="beneficiarios_provincia_buenosaires.csv"'
    )

    content = b"".join(response.streaming_content).decode("utf-8-sig")
    reader = csv.DictReader(StringIO(content), delimiter=";")
    rows = list(reader)

    assert len(rows) == 1
    assert rows[0]["CUIL"] == "20451112223"
    assert rows[0]["Apellido y Nombre"] == "Perez, Sofia"
    assert rows[0]["Provincia"] == "Buenos Aires"


@pytest.mark.django_db
def test_export_respeta_filtros_territoriales_y_nombra_archivo(
    client, usuario_con_permisos, beneficiarios
):
    beneficiario, _ = beneficiarios
    municipio = Municipio.objects.create(
        nombre="La Plata", provincia=beneficiario.provincia
    )
    localidad = Localidad.objects.create(nombre="Tolosa", municipio=municipio)
    beneficiario.municipio = municipio
    beneficiario.localidad = localidad
    beneficiario.save()

    client.force_login(usuario_con_permisos)
    response_municipio = client.get(
        reverse("beneficiarios_export"),
        {"filters": _payload("municipio", "La Plata")},
    )
    response_localidad = client.get(
        reverse("beneficiarios_export"),
        {"filters": _payload("localidad", "Tolosa")},
    )

    assert response_municipio["Content-Disposition"] == (
        'attachment; filename="beneficiarios_municipio_laplata.csv"'
    )
    assert response_localidad["Content-Disposition"] == (
        'attachment; filename="beneficiarios_localidad_tolosa.csv"'
    )

    municipio_content = b"".join(response_municipio.streaming_content).decode(
        "utf-8-sig"
    )
    localidad_content = b"".join(response_localidad.streaming_content).decode(
        "utf-8-sig"
    )
    municipio_rows = list(csv.DictReader(StringIO(municipio_content), delimiter=";"))
    localidad_rows = list(csv.DictReader(StringIO(localidad_content), delimiter=";"))

    assert [row["CUIL"] for row in municipio_rows] == ["20451112223"]
    assert [row["CUIL"] for row in localidad_rows] == ["20451112223"]


@pytest.mark.django_db
def test_export_incluye_fecha_nacimiento_y_cuil_de_responsable(
    client, usuario_con_permisos, beneficiarios
):
    client.force_login(usuario_con_permisos)
    response = client.get(reverse("beneficiarios_export"))

    content = b"".join(response.streaming_content).decode("utf-8-sig")
    rows = list(csv.DictReader(StringIO(content), delimiter=";"))
    row = next(row for row in rows if row["CUIL"] == "20451112223")

    assert row["Fecha de nacimiento"] == "04/03/2012"
    assert row["CUIL del responsable"] == "20285551113"


@pytest.mark.django_db
def test_export_respeta_orden_por_cuil_de_responsable(
    client, usuario_con_permisos, beneficiarios
):
    client.force_login(usuario_con_permisos)
    response = client.get(
        reverse("beneficiarios_export"),
        {"sort": "responsable_cuil", "direction": "desc"},
    )

    content = b"".join(response.streaming_content).decode("utf-8-sig")
    rows = list(csv.DictReader(StringIO(content), delimiter=";"))

    assert [row["CUIL del responsable"] for row in rows] == [
        "20285551114",
        "20285551113",
    ]


@pytest.mark.django_db
def test_export_respeta_orden_visible_por_cuil(
    client, usuario_con_permisos, beneficiarios
):
    client.force_login(usuario_con_permisos)
    response = client.get(
        reverse("beneficiarios_export"),
        {"sort": "cuil", "direction": "asc"},
    )

    content = b"".join(response.streaming_content).decode("utf-8-sig")
    rows = list(csv.DictReader(StringIO(content), delimiter=";"))

    assert [row["CUIL"] for row in rows] == ["20451112223", "20451112224"]


@pytest.mark.django_db
def test_export_incluye_bom_utf8_para_excel(
    client, usuario_con_permisos, beneficiarios
):
    client.force_login(usuario_con_permisos)
    response = client.get(reverse("beneficiarios_export"))

    content = b"".join(response.streaming_content)
    assert content.startswith(b"\xef\xbb\xbf")


@pytest.mark.django_db
def test_export_neutraliza_formulas_en_campos_textuales(
    client, usuario_con_permisos, beneficiarios
):
    beneficiario, _ = beneficiarios
    beneficiario.apellido = "=HIPERVINCULO()"
    beneficiario.responsable.apellido = "@referencia"
    beneficiario.save()
    beneficiario.responsable.save()

    client.force_login(usuario_con_permisos)
    response = client.get(reverse("beneficiarios_export"))

    content = b"".join(response.streaming_content).decode("utf-8-sig")
    rows = list(csv.DictReader(StringIO(content), delimiter=";"))
    row = next(row for row in rows if row["CUIL"] == "20451112223")

    assert row["Apellido y Nombre"] == "'=HIPERVINCULO(), Sofia"
    assert row["Responsable"] == "'@referencia, Marta"


@pytest.mark.django_db
def test_export_sin_resultados_no_genera_csv_y_avisa(
    client, usuario_con_permisos, beneficiarios
):
    client.force_login(usuario_con_permisos)
    response = client.get(
        reverse("beneficiarios_export"),
        {"filters": _payload("provincia", "Santa Fe")},
    )

    assert response.status_code == 302
    assert response.url == reverse("beneficiarios_list")
    assert "Content-Disposition" not in response

    seguimiento = client.get(response.url)
    mensajes = list(seguimiento.context["messages"])
    assert any("No hay beneficiarios" in str(m) for m in mensajes)


@pytest.mark.django_db
def test_export_rechaza_usuario_sin_permiso_de_exportacion(client, db):
    user = User.objects.create_user(username="cdf-sin-export", password="x")
    user.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="centrodefamilia", codename="view_centro"
        )
    )
    client.force_login(user)

    response = client.get(reverse("beneficiarios_export"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_export_rechaza_usuario_anonimo(client, db):
    response = client.get(reverse("beneficiarios_export"))
    assert response.status_code == 403


@pytest.mark.django_db
def test_beneficiarios_list_muestra_boton_exportar_con_permiso(
    client, usuario_con_permisos
):
    client.force_login(usuario_con_permisos)
    response = client.get(reverse("beneficiarios_list"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "btn-export-csv" in content
    assert reverse("beneficiarios_export") in content
    # El boton se renombro a "Exportar busqueda" y se movio de .search-actions
    # a la barra superior (.poncho-topbar), segun el prototipo de Figma.
    # Se conserva .btn-export-csv porque export_helper.js engancha por esa clase.
    assert "Exportar búsqueda" in content
    assert "poncho-topbar" in content


@pytest.mark.django_db
def test_beneficiarios_list_oculta_boton_exportar_sin_permiso(client, db):
    user = _crear_usuario_listado("cdf-list-sin-export")
    client.force_login(user)

    response = client.get(reverse("beneficiarios_list"))

    assert response.status_code == 200
    assert "btn-export-csv" not in response.content.decode()


@pytest.mark.django_db
def test_beneficiarios_list_muestra_boton_exportar_para_cdf_sse(
    client, usuario_cdf_sse
):
    client.force_login(usuario_cdf_sse)
    response = client.get(reverse("beneficiarios_list"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "btn-export-csv" in content
    assert reverse("beneficiarios_export") in content


@pytest.mark.django_db
def test_export_permite_rol_cdf_sse(client, usuario_cdf_sse, beneficiarios):
    client.force_login(usuario_cdf_sse)
    response = client.get(reverse("beneficiarios_export"))

    assert response.status_code == 200

    content = b"".join(response.streaming_content).decode("utf-8-sig")
    rows = list(csv.DictReader(StringIO(content), delimiter=";"))

    assert {row["CUIL"] for row in rows} == {"20451112223", "20451112224"}


@pytest.mark.django_db
def test_beneficiarios_list_muestra_fecha_nacimiento_y_cuil_de_responsable(
    client, usuario_con_permisos, beneficiarios
):
    client.force_login(usuario_con_permisos)
    response = client.get(reverse("beneficiarios_list"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Fecha de nacimiento" in content
    assert "CUIL del responsable" in content
    assert "04/03/2012" in content
    assert "20285551113" in content
