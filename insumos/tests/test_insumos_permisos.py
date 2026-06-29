import pytest
from django.contrib.auth.models import Permission, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from core.models import Programa
from insumos.models import Insumo, InsumoCategoria


@pytest.fixture
def programa(db):
    return Programa.objects.create(nombre="Comedores")


def _permisos(codenames):
    return Permission.objects.filter(
        content_type__app_label="insumos", codename__in=codenames
    )


@pytest.fixture
def user_gestion(db):
    user = User.objects.create_user(username="insumos-gestion", password="test1234")
    user.user_permissions.add(
        *_permisos(
            [
                "view_insumo",
                "add_insumo",
                "change_insumo",
                "delete_insumo",
                "view_insumocategoria",
                "add_insumocategoria",
                "change_insumocategoria",
                "delete_insumocategoria",
            ]
        )
    )
    return user


@pytest.fixture
def user_consulta(db):
    user = User.objects.create_user(username="insumos-consulta", password="test1234")
    user.user_permissions.add(*_permisos(["view_insumo", "view_insumocategoria"]))
    return user


def _crear_insumo(programa, *, activo=True, categoria=None, titulo="Manual"):
    archivo = SimpleUploadedFile(
        "manual.pdf", b"contenido", content_type="application/pdf"
    )
    return Insumo.objects.create(
        programa=programa,
        categoria=categoria,
        titulo=titulo,
        archivo=archivo,
        activo=activo,
    )


@pytest.mark.django_db
def test_listado_requiere_permiso(client):
    response = client.get(reverse("insumos_listar"))
    assert response.status_code == 403


@pytest.mark.django_db
def test_consulta_puede_listar(client, user_consulta, programa):
    _crear_insumo(programa)
    client.force_login(user_consulta)
    response = client.get(reverse("insumos_listar"))
    assert response.status_code == 200
    assert b"Manual" in response.content


@pytest.mark.django_db
def test_consulta_no_puede_crear_ni_gestionar_categorias(
    client, user_consulta, programa
):
    client.force_login(user_consulta)
    assert client.get(reverse("insumos_crear")).status_code == 403
    assert client.get(reverse("insumos_categorias_crear")).status_code == 403


@pytest.mark.django_db
def test_consulta_puede_descargar(client, user_consulta, programa):
    insumo = _crear_insumo(programa)
    client.force_login(user_consulta)
    response = client.get(reverse("insumos_descargar", args=[insumo.pk]))
    assert response.status_code == 200
    assert response.get("Content-Disposition", "").startswith("attachment")


@pytest.mark.django_db
def test_descarga_funciona_con_insumo_inactivo(client, user_consulta, programa):
    insumo = _crear_insumo(programa, activo=False)
    client.force_login(user_consulta)
    response = client.get(reverse("insumos_descargar", args=[insumo.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_descarga_sin_permiso_es_403(client, programa):
    insumo = _crear_insumo(programa)
    user = User.objects.create_user(username="sin-permiso", password="test1234")
    client.force_login(user)
    response = client.get(reverse("insumos_descargar", args=[insumo.pk]))
    assert response.status_code == 403


@pytest.mark.django_db
def test_gestion_puede_crear_insumo(client, user_gestion, programa):
    client.force_login(user_gestion)
    archivo = SimpleUploadedFile(
        "nuevo.pdf", b"contenido", content_type="application/pdf"
    )
    response = client.post(
        reverse("insumos_crear"),
        {
            "programa": programa.id,
            "categoria": "",
            "titulo": "Nuevo insumo",
            "descripcion": "desc",
            "activo": "on",
            "archivo": archivo,
        },
    )
    assert response.status_code == 302
    insumo = Insumo.objects.get(titulo="Nuevo insumo")
    assert insumo.usuario_creacion == user_gestion


@pytest.mark.django_db
def test_gestion_puede_crear_categoria(client, user_gestion, programa):
    client.force_login(user_gestion)
    response = client.post(
        reverse("insumos_categorias_crear"),
        {
            "programa": programa.id,
            "nombre": "Rendiciones",
            "descripcion": "",
            "orden": 1,
            "activo": "on",
        },
    )
    assert response.status_code == 302
    assert InsumoCategoria.objects.filter(nombre="Rendiciones").exists()


@pytest.mark.django_db
def test_categoria_de_otro_programa_es_invalida(client, user_gestion, programa):
    otro = Programa.objects.create(nombre="Otro programa")
    categoria = InsumoCategoria.objects.create(programa=otro, nombre="Ajena")
    client.force_login(user_gestion)
    archivo = SimpleUploadedFile("x.pdf", b"contenido", content_type="application/pdf")
    response = client.post(
        reverse("insumos_crear"),
        {
            "programa": programa.id,
            "categoria": categoria.id,
            "titulo": "Insumo inconsistente",
            "descripcion": "",
            "activo": "on",
            "archivo": archivo,
        },
    )
    assert response.status_code == 200
    assert not Insumo.objects.filter(titulo="Insumo inconsistente").exists()
