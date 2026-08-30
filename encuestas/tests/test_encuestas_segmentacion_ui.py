import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from encuestas.models import (
    Pregunta,
    SegmentacionDestinatario,
    TipoDocumento,
    TipoPregunta,
    TipoSegmentacion,
)
from encuestas.services import (
    actualizar_segmentacion,
    agregar_destinatario,
    crear_encuesta,
    publicar,
    quitar_destinatario,
)


@pytest.fixture
def usuario_creador(django_user_model):
    return django_user_model.objects.create_user(username="creador", password="x")


@pytest.fixture
def encuesta(usuario_creador):
    return crear_encuesta(
        usuario=usuario_creador,
        titulo="Satisfacción",
        es_obligatoria=True,
        duracion_ronda_dias=7,
    )


# --- servicios: agregar/quitar destinatario individual --------------------


@pytest.mark.django_db
def test_agregar_destinatario_crea_segmentacion_si_no_existe(encuesta):
    destinatario = agregar_destinatario(
        encuesta, tipo_documento="dni", numero_documento="30111222"
    )
    encuesta.refresh_from_db()
    assert encuesta.segmentacion.tipo == TipoSegmentacion.LISTADO_DOCUMENTOS
    assert destinatario.numero_documento == "30111222"


@pytest.mark.django_db
def test_agregar_destinatario_falla_si_segmentacion_es_todos_los_usuarios(encuesta):
    actualizar_segmentacion(encuesta, tipo=TipoSegmentacion.TODOS_LOS_USUARIOS)
    with pytest.raises(ValidationError):
        agregar_destinatario(encuesta, tipo_documento="dni", numero_documento="1")


@pytest.mark.django_db
def test_agregar_destinatario_tipo_invalido_falla(encuesta):
    with pytest.raises(ValidationError):
        agregar_destinatario(
            encuesta, tipo_documento="pasaporte", numero_documento="123"
        )


@pytest.mark.django_db
def test_agregar_destinatario_numero_no_numerico_falla(encuesta):
    with pytest.raises(ValidationError):
        agregar_destinatario(encuesta, tipo_documento="dni", numero_documento="abc")


@pytest.mark.django_db
def test_agregar_destinatario_es_idempotente(encuesta):
    agregar_destinatario(encuesta, tipo_documento="dni", numero_documento="1")
    agregar_destinatario(encuesta, tipo_documento="dni", numero_documento="1")
    assert (
        SegmentacionDestinatario.objects.filter(segmentacion__encuesta=encuesta).count()
        == 1
    )


@pytest.mark.django_db
def test_quitar_destinatario_elimina(encuesta):
    destinatario = agregar_destinatario(
        encuesta, tipo_documento="dni", numero_documento="1"
    )
    quitar_destinatario(encuesta, destinatario.pk)
    assert not SegmentacionDestinatario.objects.filter(pk=destinatario.pk).exists()


@pytest.mark.django_db
def test_quitar_destinatario_sin_segmentacion_falla(encuesta):
    with pytest.raises(ValidationError):
        quitar_destinatario(encuesta, 999)


@pytest.mark.django_db
def test_quitar_destinatario_inexistente_falla(encuesta):
    agregar_destinatario(encuesta, tipo_documento="dni", numero_documento="1")
    with pytest.raises(ValidationError):
        quitar_destinatario(encuesta, 999999)


@pytest.mark.django_db
def test_agregar_y_quitar_destinatario_funcionan_con_ronda_abierta(
    encuesta, usuario_creador
):
    """Regla de negocio 12: la segmentación se modifica en caliente, a
    diferencia de actualizar_encuesta/reemplazar_preguntas."""
    Pregunta.objects.create(
        encuesta=encuesta, texto="¿Todo bien?", tipo=TipoPregunta.SI_NO
    )
    actualizar_segmentacion(
        encuesta,
        tipo=TipoSegmentacion.LISTADO_DOCUMENTOS,
        destinatarios=[{"tipo_documento": TipoDocumento.DNI, "numero_documento": "1"}],
    )
    publicar(encuesta, usuario=usuario_creador)

    destinatario = agregar_destinatario(
        encuesta, tipo_documento="dni", numero_documento="2"
    )
    quitar_destinatario(encuesta, destinatario.pk)

    assert encuesta.segmentacion.destinatarios.count() == 1


# --- vistas -----------------------------------------------------------------


def _permisos(codenames):
    return Permission.objects.filter(
        content_type__app_label="encuestas", codename__in=codenames
    )


@pytest.fixture
def user_gestor(django_user_model):
    user = django_user_model.objects.create_user(username="gestor", password="test1234")
    user.user_permissions.add(
        *_permisos(["view_encuesta", "add_encuesta", "change_encuesta"])
    )
    return user


@pytest.fixture
def user_sin_permiso(django_user_model):
    return django_user_model.objects.create_user(username="sin-permiso", password="x")


@pytest.mark.django_db
def test_vista_segmentacion_requiere_permiso(client, user_sin_permiso, encuesta):
    client.force_login(user_sin_permiso)
    response = client.get(reverse("encuestas_segmentacion", args=[encuesta.pk]))
    assert response.status_code == 403


@pytest.mark.django_db
def test_vista_segmentacion_muestra_destinatarios_actuales(
    client, user_gestor, encuesta
):
    agregar_destinatario(encuesta, tipo_documento="dni", numero_documento="30111222")
    client.force_login(user_gestor)

    response = client.get(reverse("encuestas_segmentacion", args=[encuesta.pk]))

    assert response.status_code == 200
    assert b"30111222" in response.content


@pytest.mark.django_db
def test_vista_tipo_update_cambia_a_listado_documentos(client, user_gestor, encuesta):
    client.force_login(user_gestor)

    response = client.post(
        reverse("encuestas_segmentacion_tipo", args=[encuesta.pk]),
        {"tipo": "listado_documentos"},
    )

    assert response.status_code == 302
    encuesta.refresh_from_db()
    assert encuesta.segmentacion.tipo == TipoSegmentacion.LISTADO_DOCUMENTOS


@pytest.mark.django_db
def test_vista_tipo_update_con_archivo_carga_destinatarios(
    client, user_gestor, encuesta
):
    archivo = SimpleUploadedFile(
        "listado.csv",
        b"tipo_documento,numero_documento\ndni,30111222\n",
        content_type="text/csv",
    )
    client.force_login(user_gestor)

    response = client.post(
        reverse("encuestas_segmentacion_tipo", args=[encuesta.pk]),
        {"tipo": "listado_documentos", "archivo_listado": archivo},
    )

    assert response.status_code == 302
    encuesta.refresh_from_db()
    assert encuesta.segmentacion.destinatarios.filter(
        numero_documento="30111222"
    ).exists()


@pytest.mark.django_db
def test_vista_agregar_destinatario(client, user_gestor, encuesta):
    actualizar_segmentacion(encuesta, tipo=TipoSegmentacion.LISTADO_DOCUMENTOS)
    client.force_login(user_gestor)

    response = client.post(
        reverse("encuestas_segmentacion_agregar", args=[encuesta.pk]),
        {"tipo_documento": "dni", "numero_documento": "30111222"},
    )

    assert response.status_code == 302
    assert encuesta.segmentacion.destinatarios.filter(
        numero_documento="30111222"
    ).exists()


@pytest.mark.django_db
def test_vista_quitar_destinatario(client, user_gestor, encuesta):
    actualizar_segmentacion(encuesta, tipo=TipoSegmentacion.LISTADO_DOCUMENTOS)
    destinatario = agregar_destinatario(
        encuesta, tipo_documento="dni", numero_documento="30111222"
    )
    client.force_login(user_gestor)

    response = client.post(
        reverse("encuestas_segmentacion_quitar", args=[encuesta.pk, destinatario.pk])
    )

    assert response.status_code == 302
    assert not SegmentacionDestinatario.objects.filter(pk=destinatario.pk).exists()


@pytest.mark.django_db
def test_vista_agregar_y_quitar_destinatario_funcionan_con_ronda_abierta(
    client, user_gestor, encuesta
):
    Pregunta.objects.create(
        encuesta=encuesta, texto="¿Todo bien?", tipo=TipoPregunta.SI_NO
    )
    actualizar_segmentacion(
        encuesta,
        tipo=TipoSegmentacion.LISTADO_DOCUMENTOS,
        destinatarios=[{"tipo_documento": TipoDocumento.DNI, "numero_documento": "1"}],
    )
    publicar(encuesta, usuario=encuesta.usuario_creador)
    client.force_login(user_gestor)

    response = client.post(
        reverse("encuestas_segmentacion_agregar", args=[encuesta.pk]),
        {"tipo_documento": "dni", "numero_documento": "2"},
    )

    assert response.status_code == 302
    assert encuesta.segmentacion.destinatarios.count() == 2
