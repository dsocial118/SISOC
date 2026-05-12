import pytest
from django.contrib.auth.models import Permission, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from core.models import Municipio, Provincia
from dispositivos.models import Dispositivo


@pytest.fixture
def provincia_municipio(db):
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    return provincia, municipio


@pytest.fixture
def user_con_permisos(db):
    user = User.objects.create_user(username="disp-admin", password="test1234")
    perms = Permission.objects.filter(
        content_type__app_label="dispositivos",
        codename__in=[
            "add_dispositivo",
            "change_dispositivo",
            "delete_dispositivo",
            "view_dispositivo",
        ],
    )
    user.user_permissions.add(*perms)
    return user


def _crear_dispositivo(provincia, municipio, indice=0, **overrides):
    data = {
        "nombre_institucion": f"Dispositivo {indice}",
        "tipo_gestion": "estatal",
        "cuit_institucion": f"20{indice:09d}",
        "provincia": provincia,
        "municipio": municipio,
        "domicilio_institucion": f"Calle {indice}",
        "telefono_contacto": "2219876543",
        "responsable_nombre_completo": "Ana Lopez",
        "responsable_dni": f"{indice:08d}",
        "tipo_dispositivo": "refugio",
        "modalidad_funcionamiento": "permanente",
        "capacidad_total_plazas": "0_15",
    }
    data.update(overrides)
    return Dispositivo.objects.create(**data)


@pytest.mark.django_db
def test_listado_requiere_login(client):
    response = client.get(reverse("dispositivos_listar"))
    assert response.status_code == 403


@pytest.mark.django_db
def test_crud_dispositivo_con_permisos(client, user_con_permisos, provincia_municipio):
    provincia, municipio = provincia_municipio
    client.force_login(user_con_permisos)

    documento_principal = SimpleUploadedFile(
        "documento-principal.pdf", b"contenido 1", content_type="application/pdf"
    )
    documento_adicional_1 = SimpleUploadedFile(
        "documento-adicional-1.pdf", b"contenido 2", content_type="application/pdf"
    )
    documento_adicional_2 = SimpleUploadedFile(
        "documento-adicional-2.pdf", b"contenido 3", content_type="application/pdf"
    )
    documento_adicional_3 = SimpleUploadedFile(
        "documento-adicional-3.pdf", b"contenido 4", content_type="application/pdf"
    )
    documento_adicional_4 = SimpleUploadedFile(
        "documento-adicional-4.pdf", b"contenido 5", content_type="application/pdf"
    )

    create_url = reverse("dispositivos_crear")
    response_create = client.post(
        create_url,
        data={
            "nombre_institucion": "Dispositivo Test",
            "tipo_gestion": "estatal",
            "cuit_institucion": "20123456789",
            "provincia": provincia.id,
            "municipio": municipio.id,
            "domicilio_institucion": "Calle 1 123",
            "telefono_contacto": "2211234567",
            "correo_electronico": "test@example.com",
            "responsable_nombre_completo": "Juan Perez",
            "responsable_dni": "12345678",
            "tipo_dispositivo": "refugio",
            "modalidad_funcionamiento": "permanente",
            "capacidad_total_plazas": "16_30",
            "dias_atencion": ["lunes", "martes"],
            "horarios_funcionamiento": ["manana"],
            "observaciones_adicionales": "Observación de prueba",
            "documentacion_dispositivo": documento_principal,
            "documentacion_dispositivo_adicional_1": documento_adicional_1,
            "documentacion_dispositivo_adicional_2": documento_adicional_2,
            "documentacion_dispositivo_adicional_3": documento_adicional_3,
            "documentacion_dispositivo_adicional_4": documento_adicional_4,
        },
    )
    assert response_create.status_code == 302

    dispositivo = Dispositivo.objects.get(nombre_institucion="Dispositivo Test")

    detail_url = reverse("dispositivos_detalle", kwargs={"pk": dispositivo.pk})
    response_detail = client.get(detail_url)
    assert response_detail.status_code == 200
    contenido_detalle = response_detail.content.decode("utf-8")
    assert "Observación de prueba" in contenido_detalle
    assert "documento-principal.pdf" in contenido_detalle
    assert "documento-adicional-4.pdf" in contenido_detalle

    edit_url = reverse("dispositivos_editar", kwargs={"pk": dispositivo.pk})
    response_edit = client.post(
        edit_url,
        data={
            "nombre_institucion": "Dispositivo Editado",
            "tipo_gestion": "estatal",
            "cuit_institucion": "20123456789",
            "provincia": provincia.id,
            "municipio": municipio.id,
            "domicilio_institucion": "Calle 1 123",
            "telefono_contacto": "2211234567",
            "correo_electronico": "test@example.com",
            "responsable_nombre_completo": "Juan Perez",
            "responsable_dni": "12345678",
            "tipo_dispositivo": "refugio",
            "modalidad_funcionamiento": "permanente",
            "capacidad_total_plazas": "16_30",
            "dias_atencion": ["lunes"],
            "horarios_funcionamiento": ["manana"],
        },
    )
    assert response_edit.status_code == 302

    dispositivo.refresh_from_db()
    assert dispositivo.nombre_institucion == "Dispositivo Editado"

    delete_url = reverse("dispositivos_eliminar", kwargs={"pk": dispositivo.pk})
    response_delete = client.post(delete_url)
    assert response_delete.status_code == 302
    assert not Dispositivo.objects.filter(pk=dispositivo.pk).exists()


@pytest.mark.django_db
def test_sin_permiso_view_dispositivo_devuelve_403(client, provincia_municipio):
    provincia, municipio = provincia_municipio
    user = User.objects.create_user(username="sin-permiso", password="test1234")
    dispositivo = _crear_dispositivo(
        provincia,
        municipio,
        indice=11222333,
        nombre_institucion="Dispositivo Permisos",
        cuit_institucion="20111222333",
        responsable_dni="33444555",
    )

    client.force_login(user)
    response = client.get(
        reverse("dispositivos_detalle", kwargs={"pk": dispositivo.pk})
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_listado_oculta_acciones_sin_permisos_de_mutacion(client, provincia_municipio):
    provincia, municipio = provincia_municipio
    user = User.objects.create_user(username="disp-viewer", password="test1234")
    permiso_view = Permission.objects.get(
        content_type__app_label="dispositivos",
        codename="view_dispositivo",
    )
    user.user_permissions.add(permiso_view)
    _crear_dispositivo(
        provincia,
        municipio,
        indice=44556677,
        nombre_institucion="Dispositivo Solo Lectura",
        cuit_institucion="20445566777",
        responsable_dni="44556677",
    )

    client.force_login(user)
    response = client.get(reverse("dispositivos_listar"))

    assert response.status_code == 200
    contenido = response.content.decode("utf-8")
    assert "Dispositivo Solo Lectura" in contenido
    assert "Agregar dispositivo" not in contenido
    assert 'title="Editar"' not in contenido
    assert 'title="Eliminar"' not in contenido


@pytest.mark.django_db
def test_listado_renderiza_paginacion_con_mas_de_quince_dispositivos(
    client, user_con_permisos, provincia_municipio
):
    provincia, municipio = provincia_municipio
    for indice in range(1, 17):
        _crear_dispositivo(provincia, municipio, indice=indice)

    client.force_login(user_con_permisos)
    response = client.get(reverse("dispositivos_listar"))

    assert response.status_code == 200
    assert "?page=2" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_formulario_muestra_secciones_modernas(client, user_con_permisos):
    client.force_login(user_con_permisos)

    response = client.get(reverse("dispositivos_crear"))

    assert response.status_code == 200
    contenido = response.content.decode("utf-8")
    assert "Identificación del dispositivo" in contenido
    assert "Características del dispositivo" in contenido
    assert "Población destinataria" in contenido
    assert "Modalidad de ingreso" in contenido
    assert "Servicios brindados" in contenido
    assert "Sistema de registro de personas usuarias" in contenido
    assert "Infraestructura y necesidades" in contenido
    assert "Articulaciones institucionales" in contenido
    assert "Observaciones y documentación" in contenido
    assert "Progreso del Formulario" in contenido
    registro_detalle_index = contenido.index('id="registro-detalle"')
    assert (
        contenido.index('id="id_registra_informacion_personas"')
        < registro_detalle_index
    )
    assert (
        'class="d-none"'
        in contenido[registro_detalle_index : registro_detalle_index + 200]
    )
