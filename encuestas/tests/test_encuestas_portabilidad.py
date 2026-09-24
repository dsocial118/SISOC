import json

import pytest
from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from encuestas.models import Encuesta, EstadoEncuesta, TipoSegmentacion
from encuestas.services import (
    ENCUESTA_JSON_MAX_BYTES,
    exportar_encuesta,
    importar_encuesta,
    serializar_preguntas,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def gestor(django_user_model):
    user = django_user_model.objects.create_user(username="gestor_json")
    user.user_permissions.add(
        *Permission.objects.filter(
            content_type__app_label="encuestas",
            codename__in=["add_encuesta", "change_encuesta", "view_encuesta"],
        )
    )
    return user


@pytest.fixture
def payload():
    return {
        "formato": "sisoc.encuesta",
        "version_formato": 3,
        "encuesta": {
            "titulo": "Encuesta portable",
            "descripcion": "Prueba con condición y puntajes",
            "es_anonima": True,
            "es_obligatoria": False,
            "es_opcional": True,
            "intervalo_recordatorio_dias": None,
            "es_recurrente": True,
            "intervalo_recurrencia_dias": 30,
            "duracion_ronda_dias": 7,
        },
        "preguntas": [
            {
                "orden": 1,
                "texto": "¿Cómo fue la atención?",
                "tipo": "opcion_unica",
                "obligatoria": True,
                "pondera": True,
                "opciones": [
                    {"texto": "Buena", "puntaje": 10},
                    {"texto": "Mala", "puntaje": 0},
                ],
                "condicion": None,
            },
            {
                "orden": 2,
                "texto": "¿Qué mejorarías?",
                "tipo": "texto_largo",
                "obligatoria": False,
                "pondera": False,
                "opciones": [],
                "condicion": {"orden": 1, "operador": "igual", "valor": "Mala"},
            },
        ],
    }


def archivo(datos):
    return SimpleUploadedFile(
        "encuesta.json", json.dumps(datos).encode("utf-8"), "application/json"
    )


@pytest.mark.parametrize("modalidad", ["obligatoria", "opcional", "postergable"])
@pytest.mark.parametrize(
    "segmentacion", [None, "todos_los_usuarios", "listado_documentos"]
)
def test_exportar_importar_conserva_configuracion_sin_estado_operativo(
    gestor, payload, modalidad, segmentacion
):
    payload["encuesta"].update(
        es_obligatoria=modalidad == "obligatoria",
        es_opcional=modalidad == "opcional",
        intervalo_recordatorio_dias=3 if modalidad == "postergable" else None,
    )
    if segmentacion:
        payload["segmentacion"] = {
            "tipo": segmentacion,
            "destinatarios": (
                [{"tipo_documento": "dni", "numero_documento": "00000001"}]
                if segmentacion == "listado_documentos"
                else []
            ),
        }
    original = importar_encuesta(archivo(payload), usuario=gestor)
    original.estado = EstadoEncuesta.PUBLICADA
    original.save(update_fields=["estado"])
    exportado = exportar_encuesta(original, incluir_segmentacion=bool(segmentacion))
    copia = importar_encuesta(archivo(exportado), usuario=gestor)
    assert copia.pk != original.pk
    assert copia.estado == EstadoEncuesta.BORRADOR
    assert copia.version == 1 and copia.version_de_id is None
    assert copia.usuario_creador == gestor
    assert copia.modalidad == modalidad
    assert not copia.rondas.exists()
    assert serializar_preguntas(copia) == serializar_preguntas(original)
    assert exportado["encuesta"] == payload["encuesta"]
    if segmentacion:
        assert copia.segmentacion.tipo == segmentacion
        assert (
            list(
                copia.segmentacion.destinatarios.values(
                    "tipo_documento", "numero_documento"
                )
            )
            == payload["segmentacion"]["destinatarios"]
        )
    else:
        assert not hasattr(copia, "segmentacion")
    assert "segmentacion" not in exportar_encuesta(original)


@pytest.mark.parametrize("version", [1, 2])
def test_importacion_admite_versiones_anteriores(gestor, payload, version):
    payload["version_formato"] = version
    payload["encuesta"].pop("es_opcional")
    payload["encuesta"]["intervalo_recordatorio_dias"] = 3
    encuesta = importar_encuesta(archivo(payload), usuario=gestor)
    assert encuesta.modalidad == "postergable"


@pytest.mark.parametrize(
    "nombre,contenido",
    [
        ("encuesta.csv", b"{}"),
        ("encuesta.json", b"{roto"),
        ("encuesta.json", b"\xff"),
        ("encuesta.json", b"[]"),
        ("encuesta.json", b'{"formato":"otro"}'),
        ("encuesta.json", b"x" * (ENCUESTA_JSON_MAX_BYTES + 1)),
    ],
)
def test_archivo_invalido_no_crea_encuesta(gestor, nombre, contenido):
    with pytest.raises(ValidationError):
        importar_encuesta(SimpleUploadedFile(nombre, contenido), usuario=gestor)
    assert not Encuesta.objects.exists()


@pytest.mark.parametrize(
    "error",
    ["version", "campo", "pregunta", "opciones", "condicion", "longitud", "documento"],
)
def test_datos_invalidos_revierten_toda_la_importacion(gestor, payload, error):
    if error == "version":
        payload["version_formato"] = 99
    elif error == "campo":
        payload["encuesta"]["es_opcional"] = "true"
    elif error == "pregunta":
        payload["preguntas"][1]["tipo"] = "inexistente"
    elif error == "opciones":
        payload["preguntas"][0]["opciones"] = 42
    elif error == "condicion":
        payload["preguntas"][1]["condicion"]["orden"] = 99
    elif error == "longitud":
        payload["preguntas"][0]["opciones"][0]["texto"] = "x" * 201
    else:
        payload["segmentacion"] = {
            "tipo": TipoSegmentacion.LISTADO_DOCUMENTOS,
            "destinatarios": [{"tipo_documento": "dni", "numero_documento": "abc"}],
        }
    with pytest.raises(ValidationError):
        importar_encuesta(archivo(payload), usuario=gestor)
    assert not Encuesta.objects.exists()


@pytest.mark.parametrize("con_segmentacion", [False, True])
def test_importar_redirige_al_listado_con_mensaje_correcto(
    client, gestor, payload, con_segmentacion
):
    if con_segmentacion:
        payload["segmentacion"] = {"tipo": "todos_los_usuarios", "destinatarios": []}
    client.force_login(gestor)
    response = client.post(reverse("encuestas_importar"), {"archivo": archivo(payload)})
    assert response.status_code == 302
    assert response.url == reverse("encuestas_listar")
    mensaje = str(list(get_messages(response.wsgi_request))[0])
    assert (
        "con su segmentación" if con_segmentacion else "sin segmentación"
    ) in mensaje


def test_importacion_erronea_muestra_error_y_permite_reintentar(client, gestor):
    client.force_login(gestor)
    response = client.post(
        reverse("encuestas_importar"), {"archivo": archivo({"formato": "otro"})}
    )
    assert response.url == reverse("encuestas_listar")
    mensaje = list(get_messages(response.wsgi_request))[0]
    assert mensaje.level_tag == "error"
    assert not Encuesta.objects.exists()


@pytest.mark.parametrize("autorizado", [False, True])
def test_permisos_importacion_y_exportacion(
    client, gestor, payload, autorizado, django_user_model
):
    encuesta = importar_encuesta(archivo(payload), usuario=gestor)
    user = (
        gestor
        if autorizado
        else django_user_model.objects.create_user(username="sin_permiso")
    )
    client.force_login(user)
    exportacion = client.get(reverse("encuestas_exportar", args=[encuesta.pk]))
    importacion = client.post(
        reverse("encuestas_importar"), {"archivo": archivo(payload)}
    )
    assert exportacion.status_code == (200 if autorizado else 403)
    assert importacion.status_code == (302 if autorizado else 403)
    if autorizado:
        assert "attachment" in exportacion["Content-Disposition"]
        assert exportacion.json()["formato"] == "sisoc.encuesta"


def test_exportar_segmentacion_requiere_eleccion_explicita(client, gestor, payload):
    payload["segmentacion"] = {"tipo": "todos_los_usuarios", "destinatarios": []}
    encuesta = importar_encuesta(archivo(payload), usuario=gestor)
    client.force_login(gestor)
    url = reverse("encuestas_exportar", args=[encuesta.pk])
    assert "segmentacion" not in client.get(url).json()
    assert (
        client.get(url, {"incluir_segmentacion": "1"}).json()["segmentacion"]
        == payload["segmentacion"]
    )
