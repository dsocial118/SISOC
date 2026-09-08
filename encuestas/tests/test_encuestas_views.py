import json

import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse

from encuestas.models import (
    Encuesta,
    EstadoEncuesta,
    EstadoRonda,
    Pregunta,
    TipoPregunta,
    TipoSegmentacion,
)
from encuestas.services import actualizar_segmentacion, publicar


def _permisos(codenames):
    return Permission.objects.filter(
        content_type__app_label="encuestas", codename__in=codenames
    )


@pytest.fixture
def user_gestor(django_user_model):
    user = django_user_model.objects.create_user(username="gestor", password="test1234")
    user.user_permissions.add(
        *_permisos(
            [
                "view_encuesta",
                "add_encuesta",
                "change_encuesta",
                "delete_encuesta",
                "change_rondaencuesta",
            ]
        )
    )
    return user


@pytest.fixture
def user_resultados(django_user_model):
    user = django_user_model.objects.create_user(
        username="resultados", password="test1234"
    )
    user.user_permissions.add(*_permisos(["view_encuesta", "ver_resultados"]))
    return user


@pytest.fixture
def encuesta_lista(user_gestor):
    """Encuesta obligatoria y publicable, pero segmentada por un DNI que no
    pertenece a ningún usuario de estos tests (los perfiles de prueba no
    cargan dni/cuil). Estos tests ejercitan permisos de gestión, no el
    bloqueo por encuesta obligatoria (ver test_encuestas_middleware.py) — si
    usara TODOS_LOS_USUARIOS, EncuestaObligatoriaMiddleware bloquearía a
    cualquier actor de estos tests antes de llegar a la vista."""
    encuesta = Encuesta.objects.create(
        titulo="Satisfacción",
        es_obligatoria=True,
        duracion_ronda_dias=7,
        usuario_creador=user_gestor,
    )
    Pregunta.objects.create(
        encuesta=encuesta, texto="¿Todo bien?", tipo=TipoPregunta.SI_NO
    )
    actualizar_segmentacion(
        encuesta,
        tipo=TipoSegmentacion.LISTADO_DOCUMENTOS,
        destinatarios=[{"tipo_documento": "dni", "numero_documento": "00000000"}],
    )
    return encuesta


@pytest.mark.django_db
def test_listado_requiere_permiso(client):
    response = client.get(reverse("encuestas_listar"))
    assert response.status_code == 403


@pytest.mark.django_db
def test_usuario_con_ver_resultados_puede_listar(
    client, user_resultados, encuesta_lista
):
    client.force_login(user_resultados)
    response = client.get(reverse("encuestas_listar"))
    assert response.status_code == 200
    assert b"Satisfacci\xc3\xb3n" in response.content


@pytest.mark.django_db
def test_usuario_con_ver_resultados_no_ve_boton_gestionar(
    client, user_resultados, encuesta_lista
):
    client.force_login(user_resultados)
    response = client.get(reverse("encuestas_listar"))
    assert b"Generar encuesta" not in response.content


@pytest.mark.django_db
def test_usuario_sin_permiso_no_puede_crear(client, user_resultados):
    client.force_login(user_resultados)
    response = client.get(reverse("encuestas_crear"))
    assert response.status_code == 403


@pytest.mark.django_db
def test_gestor_puede_crear_encuesta(client, user_gestor):
    client.force_login(user_gestor)
    response = client.post(
        reverse("encuestas_crear"),
        {
            "titulo": "Clima laboral",
            "descripcion": "",
            "es_anonima": "on",
            "es_obligatoria": "",
            "intervalo_recordatorio_dias": 3,
            "es_recurrente": "",
            "duracion_ronda_dias": 10,
        },
    )
    assert response.status_code == 302
    encuesta = Encuesta.objects.get(titulo="Clima laboral")
    assert encuesta.usuario_creador == user_gestor
    assert encuesta.estado == EstadoEncuesta.BORRADOR
    assert encuesta.preguntas.count() == 0


@pytest.mark.django_db
def test_gestor_puede_crear_encuesta_con_preguntas_y_condicion(client, user_gestor):
    preguntas = [
        {
            "orden": 1,
            "texto": "¿Usás el módulo X?",
            "tipo": "opcion_unica",
            "obligatoria": True,
            "opciones": ["Sí", "No"],
            "condicion": None,
        },
        {
            "orden": 2,
            "texto": "¿Qué mejorarías?",
            "tipo": "texto_largo",
            "obligatoria": False,
            "opciones": [],
            "condicion": {"orden": 1, "operador": "igual", "valor": "Sí"},
        },
    ]
    client.force_login(user_gestor)
    response = client.post(
        reverse("encuestas_crear"),
        {
            "titulo": "Con preguntas",
            "descripcion": "",
            "es_anonima": "",
            "es_obligatoria": "on",
            "es_recurrente": "",
            "duracion_ronda_dias": 7,
            "preguntas_json": json.dumps(preguntas),
        },
    )
    assert response.status_code == 302
    encuesta = Encuesta.objects.get(titulo="Con preguntas")
    assert encuesta.preguntas.count() == 2
    base = encuesta.preguntas.get(orden=1)
    dependiente = encuesta.preguntas.get(orden=2)
    assert base.opciones.count() == 2
    assert dependiente.pregunta_condicion_id == base.pk
    assert dependiente.valor_condicion == "Sí"


@pytest.mark.django_db
def test_crear_encuesta_con_preguntas_json_invalido_no_guarda(client, user_gestor):
    client.force_login(user_gestor)
    response = client.post(
        reverse("encuestas_crear"),
        {
            "titulo": "Payload roto",
            "descripcion": "",
            "es_anonima": "",
            "es_obligatoria": "on",
            "es_recurrente": "",
            "duracion_ronda_dias": 7,
            "preguntas_json": "{no es json valido",
        },
    )
    assert response.status_code == 200
    assert not Encuesta.objects.filter(titulo="Payload roto").exists()


@pytest.mark.django_db
def test_gestor_puede_publicar_encuesta_lista(client, user_gestor, encuesta_lista):
    client.force_login(user_gestor)
    response = client.post(reverse("encuestas_publicar", args=[encuesta_lista.pk]))
    assert response.status_code == 302
    encuesta_lista.refresh_from_db()
    assert encuesta_lista.estado == EstadoEncuesta.PUBLICADA
    assert encuesta_lista.rondas.filter(estado=EstadoRonda.ABIERTA).count() == 1


@pytest.mark.django_db
def test_publicar_sin_preguntas_no_rompe_y_deja_mensaje(client, user_gestor):
    encuesta = Encuesta.objects.create(
        titulo="Sin preguntas",
        es_obligatoria=True,
        duracion_ronda_dias=7,
        usuario_creador=user_gestor,
    )
    client.force_login(user_gestor)
    response = client.post(reverse("encuestas_publicar", args=[encuesta.pk]))
    assert response.status_code == 302
    encuesta.refresh_from_db()
    assert encuesta.estado == EstadoEncuesta.BORRADOR


@pytest.mark.django_db
def test_publicar_requiere_permiso(client, user_resultados, encuesta_lista):
    client.force_login(user_resultados)
    response = client.post(reverse("encuestas_publicar", args=[encuesta_lista.pk]))
    assert response.status_code == 403


@pytest.mark.django_db
def test_gestor_puede_editar_encuesta_sin_rondas(client, user_gestor, encuesta_lista):
    """El hidden preguntas_json siempre viaja con el estado actual (lo arma el
    JS del editor); acá lo simulamos con la pregunta que ya tiene la fixture,
    para reflejar cómo se comporta el formulario real."""
    preguntas_actuales = [
        {
            "orden": 1,
            "texto": "¿Todo bien?",
            "tipo": "si_no",
            "obligatoria": True,
            "opciones": [],
            "condicion": None,
        }
    ]
    client.force_login(user_gestor)
    response = client.post(
        reverse("encuestas_editar", args=[encuesta_lista.pk]),
        {
            "titulo": "Satisfacción (editada)",
            "descripcion": "",
            "es_anonima": "",
            "es_obligatoria": "on",
            "es_recurrente": "",
            "duracion_ronda_dias": 7,
            "preguntas_json": json.dumps(preguntas_actuales),
        },
    )
    assert response.status_code == 302
    encuesta_lista.refresh_from_db()
    assert encuesta_lista.titulo == "Satisfacción (editada)"
    assert encuesta_lista.version == 1
    assert encuesta_lista.preguntas.count() == 1


@pytest.mark.django_db
def test_editar_con_ronda_abierta_muestra_error_y_no_guarda(
    client, user_gestor, encuesta_lista
):
    publicar(encuesta_lista, usuario=user_gestor)
    client.force_login(user_gestor)
    response = client.post(
        reverse("encuestas_editar", args=[encuesta_lista.pk]),
        {
            "titulo": "Intento de edición",
            "descripcion": "",
            "es_anonima": "",
            "es_obligatoria": "on",
            "es_recurrente": "",
            "duracion_ronda_dias": 7,
        },
    )
    assert response.status_code == 200
    encuesta_lista.refresh_from_db()
    assert encuesta_lista.titulo == "Satisfacción"


@pytest.mark.django_db
def test_cerrar_ronda_requiere_permiso(client, user_resultados, encuesta_lista):
    ronda = publicar(encuesta_lista, usuario=encuesta_lista.usuario_creador)
    client.force_login(user_resultados)
    response = client.post(reverse("encuestas_ronda_cerrar", args=[ronda.pk]))
    assert response.status_code == 403


@pytest.mark.django_db
def test_gestor_puede_cerrar_ronda(client, user_gestor, encuesta_lista):
    ronda = publicar(encuesta_lista, usuario=user_gestor)
    client.force_login(user_gestor)
    response = client.post(reverse("encuestas_ronda_cerrar", args=[ronda.pk]))
    assert response.status_code == 302
    ronda.refresh_from_db()
    assert ronda.estado == EstadoRonda.CERRADA
