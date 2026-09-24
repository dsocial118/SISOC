from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from encuestas.forms import EncuestaForm
from encuestas.models import (
    CumplimientoRonda,
    Pregunta,
    RecordatorioUsuario,
    RespuestaRonda,
)
from encuestas.services import (
    actualizar_segmentacion,
    crear_encuesta,
    descartar_ronda,
    get_rondas_pendientes,
    nueva_version,
    posponer_ronda,
    procesar_rondas_pendientes,
    publicar,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def usuario(django_user_model):
    return django_user_model.objects.create_user(username="opcional")


@pytest.fixture
def ronda(usuario):
    encuesta = crear_encuesta(
        usuario=usuario,
        titulo="Encuesta opcional",
        es_opcional=True,
        es_recurrente=True,
        intervalo_recurrencia_dias=7,
        duracion_ronda_dias=3,
    )
    Pregunta.objects.create(
        encuesta=encuesta, texto="¿Todo bien?", tipo="si_no", orden=1
    )
    actualizar_segmentacion(encuesta, tipo="todos_los_usuarios")
    return publicar(encuesta, usuario=usuario)


@pytest.mark.parametrize("modalidad", ["obligatoria", "opcional", "postergable"])
def test_formulario_guarda_modalidad_y_solo_conserva_recordatorio_postergable(
    usuario, modalidad
):
    form = EncuestaForm(
        data={
            "titulo": "Modalidad",
            "modalidad": modalidad,
            "duracion_ronda_dias": 7,
            "intervalo_recordatorio_dias": 3,
        }
    )
    assert form.is_valid(), form.errors
    encuesta = crear_encuesta(usuario=usuario, **form.cleaned_data)
    assert encuesta.modalidad == modalidad
    assert encuesta.intervalo_recordatorio_dias == (
        3 if modalidad == "postergable" else None
    )
    assert EncuestaForm(instance=encuesta)["modalidad"].value() == modalidad


@pytest.mark.parametrize("intervalo", [None, 0, -1])
def test_postergable_requiere_recordatorio_positivo(intervalo):
    form = EncuestaForm(
        data={
            "titulo": "Inválida",
            "modalidad": "postergable",
            "duracion_ronda_dias": 7,
            "intervalo_recordatorio_dias": intervalo,
        }
    )
    assert not form.is_valid()
    assert "intervalo_recordatorio_dias" in form.errors


def test_no_puede_ser_opcional_y_obligatoria(usuario):
    with pytest.raises(ValidationError):
        crear_encuesta(
            usuario=usuario,
            titulo="Inválida",
            es_opcional=True,
            es_obligatoria=True,
            duracion_ronda_dias=7,
        )


def test_descartar_no_cuenta_como_respuesta_y_solo_afecta_al_usuario(
    usuario, ronda, django_user_model
):
    otro = django_user_model.objects.create_user(username="otro")
    assert get_rondas_pendientes(usuario) == [ronda]
    descartar_ronda(ronda, usuario)
    descartar_ronda(ronda, usuario)
    assert get_rondas_pendientes(usuario) == []
    assert get_rondas_pendientes(otro) == [ronda]
    assert RecordatorioUsuario.objects.filter(ronda=ronda, usuario=usuario).count() == 1
    assert not CumplimientoRonda.objects.exists()
    assert not RespuestaRonda.objects.exists()


def test_descartar_no_oculta_la_siguiente_ronda_recurrente(usuario, ronda):
    descartar_ronda(ronda, usuario)
    ronda.fecha_apertura = timezone.now() - timedelta(days=8)
    ronda.fecha_cierre_programada = timezone.now() - timedelta(days=1)
    ronda.save()
    resultado = procesar_rondas_pendientes()
    assert resultado == {"rondas_cerradas": 1, "rondas_abiertas": 1}
    pendientes = get_rondas_pendientes(usuario)
    assert len(pendientes) == 1
    assert pendientes[0].numero_ronda == 2
    assert pendientes[0].encuesta_id == ronda.encuesta_id


@pytest.mark.parametrize(
    "caso", ["obligatoria", "postergable", "ajeno", "cerrada", "vencida", "respondida"]
)
def test_descartar_rechaza_acciones_no_permitidas(usuario, ronda, caso):
    if caso in ("obligatoria", "postergable"):
        ronda.encuesta.es_opcional = False
        ronda.encuesta.es_obligatoria = caso == "obligatoria"
        ronda.encuesta.save()
    elif caso == "ajeno":
        actualizar_segmentacion(
            ronda.encuesta, tipo="listado_documentos", destinatarios=[]
        )
        ronda.refresh_from_db()
    elif caso == "cerrada":
        ronda.estado = "cerrada"
        ronda.save()
    elif caso == "vencida":
        ronda.fecha_cierre_programada = timezone.now() - timedelta(seconds=1)
        ronda.save()
    else:
        CumplimientoRonda.objects.create(ronda=ronda, usuario=usuario)
    with pytest.raises(ValidationError):
        descartar_ronda(ronda, usuario)
    assert not RecordatorioUsuario.objects.exists()


def test_no_se_puede_posponer_una_opcional(usuario, ronda):
    with pytest.raises(ValidationError):
        posponer_ronda(ronda, usuario)


def test_versionado_conserva_modalidad_opcional(usuario, ronda):
    ronda.estado = "cerrada"
    ronda.save()
    copia = nueva_version(ronda.encuesta, usuario=usuario)
    assert copia.modalidad == "opcional"
    assert copia.intervalo_recordatorio_dias is None


def test_descartar_desde_modal_redirige_y_no_vuelve_a_mostrarlo(client, usuario, ronda):
    client.force_login(usuario)
    pagina = client.get(reverse("inicio"))
    assert b"Prefiero no responder" in pagina.content
    response = client.post(
        reverse("encuestas_responder_descartar", args=[ronda.pk]),
        {"next": "https://externo.example/"},
    )
    assert response.url == reverse("inicio")
    assert get_rondas_pendientes(usuario) == []
    assert b"modal-encuesta-pendiente" not in client.get(reverse("inicio")).content


def test_descartar_requiere_login_y_post(client, usuario, ronda):
    url = reverse("encuestas_responder_descartar", args=[ronda.pk])
    assert reverse("login") in client.post(url).url
    client.force_login(usuario)
    assert client.get(url).status_code == 405
