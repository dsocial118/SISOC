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


WRAPPERS_OTRO = [
    "wrapper-tipo_gestion_otra",
    "wrapper-tipo_dispositivo_otro",
    "wrapper-poblacion_destinataria_otro",
    "wrapper-tiempo_permanencia_otro",
    "wrapper-modalidad_ingreso_otro",
    "wrapper-documentacion_ingreso_otro",
    "wrapper-requisitos_ingreso_otro",
    "wrapper-servicios_brindados_otro",
    "wrapper-tipos_actividades_formativas_otro",
    "wrapper-modo_registro_otro",
    "wrapper-tipo_informacion_registrada_otro",
    "wrapper-infraestructura_disponible_otro",
    "wrapper-infraestructura_accesibilidad_otro",
    "wrapper-articulaciones_institucionales_otro",
]


def _tag_for(contenido, wrapper_id):
    needle = f'id="{wrapper_id}"'
    idx = contenido.find(needle)
    assert idx != -1, f"No se encontró {wrapper_id} en el template"
    tag_end = contenido.find(">", idx)
    return contenido[idx:tag_end]


def _doc_slot_tag(contenido, field):
    needle = f'data-field="{field}"'
    idx = contenido.find(needle)
    assert idx != -1, f"No se encontró slot {field} en el template"
    tag_start = contenido.rfind("<div", 0, idx)
    tag_end = contenido.find(">", idx)
    return contenido[tag_start:tag_end]


@pytest.mark.django_db
def test_formulario_oculta_todos_los_wrappers_otro_en_creacion(
    client, user_con_permisos
):
    client.force_login(user_con_permisos)

    response = client.get(reverse("dispositivos_crear"))

    assert response.status_code == 200
    contenido = response.content.decode("utf-8")
    for wrapper_id in WRAPPERS_OTRO:
        tag = _tag_for(contenido, wrapper_id)
        assert "d-none" in tag, f"{wrapper_id} debe iniciar con d-none"


@pytest.mark.django_db
def test_formulario_muestra_wrappers_otro_cuando_dispositivo_tiene_valor(
    client, user_con_permisos, provincia_municipio
):
    provincia, municipio = provincia_municipio
    client.force_login(user_con_permisos)

    dispositivo = _crear_dispositivo(
        provincia,
        municipio,
        indice=99887766,
        nombre_institucion="Dispositivo Otros",
        cuit_institucion="20998877661",
        responsable_dni="99887766",
        tipo_gestion="otra",
        tipo_gestion_otra="Cooperativa local",
        tipo_dispositivo="otro",
        tipo_dispositivo_otro="Centro mixto",
        poblacion_destinataria=["otro"],
        poblacion_destinataria_otro="Personas migrantes",
        tiempo_permanencia_promedio="otro",
        tiempo_permanencia_otro="Variable",
        modalidad_ingreso=["otro"],
        modalidad_ingreso_otro="Acuerdo municipal",
        documentacion_ingreso=["otro"],
        documentacion_ingreso_otro="Acta",
        requisitos_ingreso=["otro"],
        requisitos_ingreso_otro="Compromiso",
        servicios_brindados=["otro"],
        servicios_brindados_otro="Talleres",
        registra_informacion_personas="si",
        modo_registro="otro",
        modo_registro_otro="Sistema propio",
        tipo_informacion_registrada=["otro"],
        tipo_informacion_registrada_otro="Trayectoria",
        infraestructura_disponible=["otro"],
        infraestructura_disponible_otro="Patio",
        infraestructura_accesibilidad=["otro"],
        infraestructura_accesibilidad_otro="Ascensor",
        articulaciones_institucionales=["otro"],
        articulaciones_institucionales_otro="Iglesia local",
        ofrece_actividades_formativas="si",
        tipos_actividades_formativas=["otro"],
        tipos_actividades_formativas_otro="Talleres ad-hoc",
    )

    response = client.get(reverse("dispositivos_editar", kwargs={"pk": dispositivo.pk}))

    assert response.status_code == 200
    contenido = response.content.decode("utf-8")
    for wrapper_id in WRAPPERS_OTRO:
        tag = _tag_for(contenido, wrapper_id)
        assert (
            "d-none" not in tag
        ), f"{wrapper_id} no debe tener d-none cuando 'otro' está seleccionado"


@pytest.mark.django_db
def test_formulario_solo_muestra_primer_slot_documento_en_creacion(
    client, user_con_permisos
):
    client.force_login(user_con_permisos)

    response = client.get(reverse("dispositivos_crear"))

    assert response.status_code == 200
    contenido = response.content.decode("utf-8")
    principal_tag = _doc_slot_tag(contenido, "documentacion_dispositivo")
    assert "d-none" not in principal_tag, "El slot principal debe ser visible"

    for field in [
        "documentacion_dispositivo_adicional_1",
        "documentacion_dispositivo_adicional_2",
        "documentacion_dispositivo_adicional_3",
        "documentacion_dispositivo_adicional_4",
    ]:
        tag = _doc_slot_tag(contenido, field)
        assert "d-none" in tag, f"Slot {field} debe iniciar oculto"

    assert 'id="btn-add-doc"' in contenido
    assert "Añadir archivo" in contenido


@pytest.mark.django_db
def test_formulario_muestra_slots_con_documentacion_persistida_en_edicion(
    client, user_con_permisos, provincia_municipio
):
    provincia, municipio = provincia_municipio
    client.force_login(user_con_permisos)

    dispositivo = _crear_dispositivo(
        provincia,
        municipio,
        indice=55667788,
        nombre_institucion="Dispositivo con docs",
        cuit_institucion="20556677881",
        responsable_dni="55667788",
    )
    dispositivo.documentacion_dispositivo_adicional_2.save(
        "doc-2.pdf",
        SimpleUploadedFile("doc-2.pdf", b"x", content_type="application/pdf"),
        save=True,
    )

    response = client.get(reverse("dispositivos_editar", kwargs={"pk": dispositivo.pk}))

    assert response.status_code == 200
    contenido = response.content.decode("utf-8")
    tag_2 = _doc_slot_tag(contenido, "documentacion_dispositivo_adicional_2")
    assert "d-none" not in tag_2, "El slot con archivo persistido debe ser visible"
    tag_3 = _doc_slot_tag(contenido, "documentacion_dispositivo_adicional_3")
    assert "d-none" in tag_3, "Slots sin archivo deben mantenerse ocultos"
