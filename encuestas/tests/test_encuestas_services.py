import csv
import io
import json

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from encuestas.models import (
    Encuesta,
    EstadoEncuesta,
    EstadoRonda,
    OperadorCondicion,
    Pregunta,
    TipoDocumento,
    TipoPregunta,
    TipoSegmentacion,
)
from encuestas.services import (
    RondaAbiertaError,
    abrir_ronda,
    actualizar_encuesta,
    actualizar_segmentacion,
    cerrar_ronda,
    crear_encuesta,
    nueva_version,
    publicar,
    reemplazar_preguntas,
    serializar_preguntas,
)
from encuestas.validators import (
    OPERADORES_CONDICION_VALIDOS,
    TIPOS_DOCUMENTO_VALIDOS,
    TIPOS_PREGUNTA_VALIDOS,
    parse_preguntas_payload,
)


def test_tipos_documento_validos_sincronizado_con_el_modelo():
    """validators.py duplica estos valores a propósito para evitar un import
    circular con models.py; si este test falla, actualizá ambos lados."""
    assert set(TIPOS_DOCUMENTO_VALIDOS) == {choice.value for choice in TipoDocumento}


def test_tipos_pregunta_validos_sincronizado_con_el_modelo():
    assert set(TIPOS_PREGUNTA_VALIDOS) == {choice.value for choice in TipoPregunta}


def test_operadores_condicion_validos_sincronizado_con_el_modelo():
    assert set(OPERADORES_CONDICION_VALIDOS) == {
        choice.value for choice in OperadorCondicion
    }


@pytest.fixture
def usuario(django_user_model):
    return django_user_model.objects.create_user(username="gestor", password="x")


@pytest.fixture
def encuesta(usuario):
    return crear_encuesta(
        usuario=usuario,
        titulo="Satisfacción",
        es_obligatoria=True,
        duracion_ronda_dias=7,
    )


@pytest.fixture
def encuesta_lista(encuesta):
    """Encuesta con lo mínimo para poder publicarse (pregunta + segmentación)."""
    Pregunta.objects.create(
        encuesta=encuesta, texto="¿Todo bien?", tipo=TipoPregunta.SI_NO
    )
    actualizar_segmentacion(encuesta, tipo=TipoSegmentacion.TODOS_LOS_USUARIOS)
    return encuesta


@pytest.mark.django_db
def test_crear_encuesta_asigna_usuario_creador(usuario):
    encuesta = crear_encuesta(
        usuario=usuario, titulo="Clima", es_obligatoria=True, duracion_ronda_dias=5
    )
    assert encuesta.usuario_creador == usuario
    assert encuesta.usuario_ultima_modificacion == usuario
    assert encuesta.version == 1
    assert encuesta.estado == EstadoEncuesta.BORRADOR


@pytest.mark.django_db
def test_publicar_falla_sin_preguntas(encuesta, usuario):
    with pytest.raises(ValidationError):
        publicar(encuesta, usuario=usuario)


@pytest.mark.django_db
def test_publicar_falla_sin_segmentacion(encuesta, usuario):
    Pregunta.objects.create(
        encuesta=encuesta, texto="¿Todo bien?", tipo=TipoPregunta.SI_NO
    )
    with pytest.raises(ValidationError):
        publicar(encuesta, usuario=usuario)


@pytest.mark.django_db
def test_publicar_abre_la_primera_ronda(encuesta_lista, usuario):
    ronda = publicar(encuesta_lista, usuario=usuario)

    encuesta_lista.refresh_from_db()
    assert encuesta_lista.estado == EstadoEncuesta.PUBLICADA
    assert ronda.numero_ronda == 1
    assert ronda.estado == EstadoRonda.ABIERTA


@pytest.mark.django_db
def test_publicar_dos_veces_falla(encuesta_lista, usuario):
    publicar(encuesta_lista, usuario=usuario)

    with pytest.raises(ValidationError):
        publicar(encuesta_lista, usuario=usuario)


@pytest.mark.django_db
def test_abrir_ronda_falla_si_encuesta_no_esta_publicada(encuesta):
    with pytest.raises(ValidationError):
        abrir_ronda(encuesta)


@pytest.mark.django_db
def test_abrir_ronda_falla_si_ya_hay_una_abierta(encuesta_lista, usuario):
    publicar(encuesta_lista, usuario=usuario)
    with pytest.raises(RondaAbiertaError):
        abrir_ronda(encuesta_lista)


@pytest.mark.django_db
def test_cerrar_ronda_marca_estado_y_fecha(encuesta_lista, usuario):
    ronda = publicar(encuesta_lista, usuario=usuario)
    cerrar_ronda(ronda, manual=True)
    ronda.refresh_from_db()
    assert ronda.estado == EstadoRonda.CERRADA
    assert ronda.cerrada_manualmente is True
    assert ronda.fecha_cierre_real is not None


@pytest.mark.django_db
def test_cerrar_ronda_ya_cerrada_falla(encuesta_lista, usuario):
    ronda = publicar(encuesta_lista, usuario=usuario)
    cerrar_ronda(ronda)
    with pytest.raises(ValidationError):
        cerrar_ronda(ronda)


@pytest.mark.django_db
def test_abrir_segunda_ronda_tras_cerrar_la_primera(encuesta_lista, usuario):
    primera = publicar(encuesta_lista, usuario=usuario)
    cerrar_ronda(primera)

    segunda = abrir_ronda(encuesta_lista)

    assert segunda.numero_ronda == 2
    assert segunda.estado == EstadoRonda.ABIERTA


@pytest.mark.django_db
def test_actualizar_encuesta_en_lugar_si_no_tiene_rondas(encuesta, usuario):
    actualizada = actualizar_encuesta(encuesta, usuario=usuario, titulo="Nuevo título")
    assert actualizada.pk == encuesta.pk
    assert actualizada.titulo == "Nuevo título"
    assert actualizada.version == 1


@pytest.mark.django_db
def test_actualizar_encuesta_con_ronda_abierta_falla(encuesta_lista, usuario):
    publicar(encuesta_lista, usuario=usuario)
    with pytest.raises(RondaAbiertaError):
        actualizar_encuesta(encuesta_lista, usuario=usuario, titulo="Otro título")


@pytest.mark.django_db
def test_actualizar_encuesta_con_ronda_cerrada_crea_nueva_version(
    encuesta_lista, usuario
):
    ronda = publicar(encuesta_lista, usuario=usuario)
    cerrar_ronda(ronda)

    nueva = actualizar_encuesta(
        encuesta_lista, usuario=usuario, titulo="Título editado"
    )

    assert nueva.pk != encuesta_lista.pk
    assert nueva.version == 2
    assert nueva.version_de_id == encuesta_lista.pk
    assert nueva.titulo == "Título editado"
    assert nueva.estado == EstadoEncuesta.BORRADOR


@pytest.mark.django_db
def test_nueva_version_clona_preguntas_opciones_y_condicion(encuesta, usuario):
    base = Pregunta.objects.create(
        encuesta=encuesta,
        texto="¿Usás el módulo X?",
        tipo=TipoPregunta.OPCION_UNICA,
        orden=1,
    )
    base.opciones.create(texto="Sí", valor="si", orden=1)
    base.opciones.create(texto="No", valor="no", orden=2)
    dependiente = Pregunta.objects.create(
        encuesta=encuesta,
        texto="¿Qué mejorarías?",
        tipo=TipoPregunta.TEXTO_LARGO,
        orden=2,
        pregunta_condicion=base,
        operador_condicion=OperadorCondicion.IGUAL,
        valor_condicion="si",
    )
    actualizar_segmentacion(encuesta, tipo=TipoSegmentacion.TODOS_LOS_USUARIOS)
    ronda = publicar(encuesta, usuario=usuario)
    cerrar_ronda(ronda)

    nueva = actualizar_encuesta(encuesta, usuario=usuario)

    assert nueva.preguntas.count() == 2
    nueva_base = nueva.preguntas.get(texto=base.texto)
    nueva_dependiente = nueva.preguntas.get(texto=dependiente.texto)
    assert nueva_base.opciones.count() == 2
    assert nueva_dependiente.pregunta_condicion_id == nueva_base.pk
    assert nueva_dependiente.operador_condicion == OperadorCondicion.IGUAL
    assert nueva.segmentacion.tipo == TipoSegmentacion.TODOS_LOS_USUARIOS


@pytest.mark.django_db
def test_actualizar_segmentacion_con_lista_explicita(encuesta):
    segmentacion = actualizar_segmentacion(
        encuesta,
        tipo=TipoSegmentacion.LISTADO_DOCUMENTOS,
        destinatarios=[
            {"tipo_documento": TipoDocumento.DNI, "numero_documento": "30111222"},
            {"tipo_documento": TipoDocumento.DNI, "numero_documento": "30111333"},
        ],
    )
    assert segmentacion.destinatarios.count() == 2

    # Sincronizar con una lista nueva quita el que ya no está y agrega el nuevo.
    actualizar_segmentacion(
        encuesta,
        tipo=TipoSegmentacion.LISTADO_DOCUMENTOS,
        destinatarios=[
            {"tipo_documento": TipoDocumento.DNI, "numero_documento": "30111222"},
            {"tipo_documento": TipoDocumento.CUIL, "numero_documento": "20111222339"},
        ],
    )
    numeros = set(
        segmentacion.destinatarios.values_list("tipo_documento", "numero_documento")
    )
    assert numeros == {("dni", "30111222"), ("cuil", "20111222339")}


@pytest.mark.django_db
def test_actualizar_segmentacion_todos_los_usuarios_borra_destinatarios(encuesta):
    actualizar_segmentacion(
        encuesta,
        tipo=TipoSegmentacion.LISTADO_DOCUMENTOS,
        destinatarios=[{"tipo_documento": TipoDocumento.DNI, "numero_documento": "1"}],
    )
    segmentacion = actualizar_segmentacion(
        encuesta, tipo=TipoSegmentacion.TODOS_LOS_USUARIOS
    )
    assert segmentacion.destinatarios.count() == 0


@pytest.mark.django_db
def test_actualizar_segmentacion_desde_archivo_csv(encuesta):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["tipo_documento", "numero_documento"])
    writer.writerow(["dni", "30111222"])
    writer.writerow(["cuit", "20111222339"])
    archivo = SimpleUploadedFile(
        "listado.csv", buffer.getvalue().encode("utf-8"), content_type="text/csv"
    )

    segmentacion = actualizar_segmentacion(
        encuesta, tipo=TipoSegmentacion.LISTADO_DOCUMENTOS, archivo=archivo
    )

    assert segmentacion.destinatarios.count() == 2
    assert segmentacion.destinatarios.filter(numero_documento="30111222").exists()


@pytest.mark.django_db
def test_actualizar_segmentacion_archivo_con_tipo_invalido_falla(encuesta):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["tipo_documento", "numero_documento"])
    writer.writerow(["pasaporte", "30111222"])
    archivo = SimpleUploadedFile(
        "listado.csv", buffer.getvalue().encode("utf-8"), content_type="text/csv"
    )

    with pytest.raises(ValidationError):
        actualizar_segmentacion(
            encuesta, tipo=TipoSegmentacion.LISTADO_DOCUMENTOS, archivo=archivo
        )


@pytest.mark.django_db
def test_parse_preguntas_payload_acepta_lista_vacia():
    """Una encuesta puede guardarse como borrador sin preguntas todavía."""
    assert parse_preguntas_payload("[]") == []
    assert parse_preguntas_payload("") == []


def test_parse_preguntas_payload_json_invalido_falla():
    with pytest.raises(ValidationError):
        parse_preguntas_payload("{esto no es json valido")


def test_parse_preguntas_payload_condicion_hacia_adelante_falla():
    payload = json.dumps(
        [
            {
                "orden": 1,
                "texto": "¿Qué mejorarías?",
                "tipo": "texto_largo",
                "obligatoria": False,
                "opciones": [],
                "condicion": {"orden": 2, "operador": "igual", "valor": "Sí"},
            },
            {
                "orden": 2,
                "texto": "¿Usás el módulo X?",
                "tipo": "si_no",
                "obligatoria": True,
                "opciones": [],
                "condicion": None,
            },
        ]
    )
    with pytest.raises(ValidationError):
        parse_preguntas_payload(payload)


def test_parse_preguntas_payload_opcion_unica_requiere_dos_opciones():
    payload = json.dumps(
        [
            {
                "orden": 1,
                "texto": "¿Cómo calificás el servicio?",
                "tipo": "opcion_unica",
                "obligatoria": True,
                "opciones": ["Muy bueno"],
                "condicion": None,
            }
        ]
    )
    with pytest.raises(ValidationError):
        parse_preguntas_payload(payload)


@pytest.mark.django_db
def test_reemplazar_preguntas_crea_preguntas_opciones_y_condicion(encuesta):
    payload = json.dumps(
        [
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
    )

    reemplazar_preguntas(encuesta, payload)

    assert encuesta.preguntas.count() == 2
    base = encuesta.preguntas.get(orden=1)
    dependiente = encuesta.preguntas.get(orden=2)
    assert list(base.opciones.values_list("texto", flat=True)) == ["Sí", "No"]
    assert dependiente.pregunta_condicion_id == base.pk
    assert dependiente.operador_condicion == OperadorCondicion.IGUAL
    assert dependiente.valor_condicion == "Sí"


@pytest.mark.django_db
def test_reemplazar_preguntas_pisa_las_anteriores(encuesta):
    reemplazar_preguntas(
        encuesta,
        json.dumps(
            [
                {
                    "orden": 1,
                    "texto": "Pregunta vieja",
                    "tipo": "si_no",
                    "obligatoria": True,
                    "opciones": [],
                    "condicion": None,
                }
            ]
        ),
    )
    reemplazar_preguntas(
        encuesta,
        json.dumps(
            [
                {
                    "orden": 1,
                    "texto": "Pregunta nueva",
                    "tipo": "si_no",
                    "obligatoria": True,
                    "opciones": [],
                    "condicion": None,
                }
            ]
        ),
    )

    assert encuesta.preguntas.count() == 1
    assert encuesta.preguntas.get().texto == "Pregunta nueva"


@pytest.mark.django_db
def test_reemplazar_preguntas_falla_con_ronda_abierta(encuesta_lista, usuario):
    publicar(encuesta_lista, usuario=usuario)
    with pytest.raises(RondaAbiertaError):
        reemplazar_preguntas(encuesta_lista, "[]")


@pytest.mark.django_db
def test_serializar_preguntas_coincide_con_lo_persistido(encuesta):
    payload = json.dumps(
        [
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
    )
    reemplazar_preguntas(encuesta, payload)

    serializado = serializar_preguntas(encuesta)

    assert serializado[0]["texto"] == "¿Usás el módulo X?"
    assert serializado[0]["opciones"] == [
        {"texto": "Sí", "puntaje": 0},
        {"texto": "No", "puntaje": 0},
    ]
    assert serializado[1]["condicion"] == {
        "orden": 1,
        "operador": "igual",
        "valor": "Sí",
    }
