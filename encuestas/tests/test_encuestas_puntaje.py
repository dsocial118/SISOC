import json

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.datastructures import MultiValueDict

from encuestas.models import (
    OpcionPregunta,
    OperadorCondicion,
    Pregunta,
    TipoDocumento,
    TipoPregunta,
    TipoSegmentacion,
)
from encuestas.services import (
    actualizar_encuesta,
    actualizar_segmentacion,
    cerrar_ronda,
    crear_encuesta,
    publicar,
    registrar_respuesta,
    reemplazar_preguntas,
    serializar_preguntas,
)
from encuestas.services_resultados import (
    build_export_headers,
    build_export_rows,
    encuesta_pondera,
    get_puntajes_ronda,
    puntaje_total_posible,
)
from encuestas.validators import parse_preguntas_payload


@pytest.fixture
def usuario_creador(django_user_model):
    return django_user_model.objects.create_user(username="creador", password="x")


@pytest.fixture
def respondientes(django_user_model):
    """DNI propio para que EncuestaObligatoriaMiddleware no bloquee otros
    tests HTTP (mismo motivo que en test_encuestas_resultados.py)."""
    usuarios = []
    for i in range(3):
        usuario = django_user_model.objects.create_user(
            username=f"puntaje-resp{i}", password="x"
        )
        usuario.profile.dni = f"5000000{i}"
        usuario.profile.save()
        usuarios.append(usuario)
    return usuarios


@pytest.fixture
def encuesta(usuario_creador):
    return crear_encuesta(
        usuario=usuario_creador,
        titulo="Encuesta con puntaje",
        es_obligatoria=True,
        duracion_ronda_dias=7,
    )


# ---------------------------------------------------------------------------
# Modelo
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_pondera_rechaza_tipos_no_ponderables(encuesta):
    pregunta = Pregunta(
        encuesta=encuesta,
        texto="Comentario",
        tipo=TipoPregunta.TEXTO_LARGO,
        pondera=True,
    )
    with pytest.raises(ValidationError):
        pregunta.full_clean()


@pytest.mark.django_db
def test_pondera_permite_tipos_con_valores_fijos(encuesta):
    pregunta = Pregunta(
        encuesta=encuesta, texto="¿Todo bien?", tipo=TipoPregunta.SI_NO, pondera=True
    )
    pregunta.full_clean()  # no debe lanzar


@pytest.mark.django_db
def test_puntaje_si_no_solo_aplica_a_tipo_si_no(encuesta):
    pregunta = Pregunta(
        encuesta=encuesta,
        texto="Puntuá del 1 al 10",
        tipo=TipoPregunta.ESCALA,
        pondera=True,
        puntaje_si=10,
    )
    with pytest.raises(ValidationError):
        pregunta.full_clean()


@pytest.mark.django_db
def test_opcion_pregunta_puntaje_default_cero(encuesta):
    pregunta = Pregunta.objects.create(
        encuesta=encuesta, texto="¿Cómo calificás?", tipo=TipoPregunta.OPCION_UNICA
    )
    opcion = OpcionPregunta.objects.create(
        pregunta=pregunta, texto="Bueno", valor="Bueno"
    )
    assert opcion.puntaje == 0


# ---------------------------------------------------------------------------
# validators.parse_preguntas_payload
# ---------------------------------------------------------------------------


def test_parse_preguntas_payload_pondera_rechaza_tipo_no_ponderable():
    payload = json.dumps(
        [
            {
                "orden": 1,
                "texto": "Comentario",
                "tipo": "texto_largo",
                "obligatoria": False,
                "opciones": [],
                "pondera": True,
                "condicion": None,
            }
        ]
    )
    with pytest.raises(ValidationError):
        parse_preguntas_payload(payload)


def test_parse_preguntas_payload_acepta_opciones_como_texto_plano_o_dict():
    """Compatibilidad: una opción puede llegar como string suelto (formato
    anterior, puntaje 0 implícito) o como {texto, puntaje}."""
    payload = json.dumps(
        [
            {
                "orden": 1,
                "texto": "¿Cómo calificás?",
                "tipo": "opcion_unica",
                "obligatoria": True,
                "opciones": ["Bueno", {"texto": "Malo", "puntaje": 5}],
                "pondera": True,
                "condicion": None,
            }
        ]
    )
    preguntas = parse_preguntas_payload(payload)
    opciones = preguntas[0].opciones
    assert opciones[0].texto == "Bueno" and opciones[0].puntaje == 0
    assert opciones[1].texto == "Malo" and opciones[1].puntaje == 5


def test_parse_preguntas_payload_puntaje_si_no():
    payload = json.dumps(
        [
            {
                "orden": 1,
                "texto": "¿Todo bien?",
                "tipo": "si_no",
                "obligatoria": True,
                "opciones": [],
                "pondera": True,
                "puntaje_si": 10,
                "puntaje_no": 0,
                "condicion": None,
            }
        ]
    )
    preguntas = parse_preguntas_payload(payload)
    assert preguntas[0].pondera is True
    assert preguntas[0].puntaje_si == 10
    assert preguntas[0].puntaje_no == 0


def test_parse_preguntas_payload_puntaje_negativo_falla():
    payload = json.dumps(
        [
            {
                "orden": 1,
                "texto": "¿Todo bien?",
                "tipo": "si_no",
                "obligatoria": True,
                "opciones": [],
                "pondera": True,
                "puntaje_si": -5,
                "puntaje_no": 0,
                "condicion": None,
            }
        ]
    )
    with pytest.raises(ValidationError):
        parse_preguntas_payload(payload)


def test_parse_preguntas_payload_sin_pondera_ignora_puntaje_si_no():
    payload = json.dumps(
        [
            {
                "orden": 1,
                "texto": "¿Todo bien?",
                "tipo": "si_no",
                "obligatoria": True,
                "opciones": [],
                "pondera": False,
                "puntaje_si": 10,
                "condicion": None,
            }
        ]
    )
    preguntas = parse_preguntas_payload(payload)
    assert preguntas[0].puntaje_si is None
    assert preguntas[0].puntaje_no is None


# ---------------------------------------------------------------------------
# services: reemplazar_preguntas / serializar_preguntas / nueva_version
# ---------------------------------------------------------------------------


def _payload_con_puntaje():
    return json.dumps(
        [
            {
                "orden": 1,
                "texto": "¿Cómo calificás?",
                "tipo": "opcion_unica",
                "obligatoria": True,
                "opciones": [
                    {"texto": "Bueno", "puntaje": 10},
                    {"texto": "Malo", "puntaje": 0},
                ],
                "pondera": True,
                "condicion": None,
            },
            {
                "orden": 2,
                "texto": "¿Volverías?",
                "tipo": "si_no",
                "obligatoria": True,
                "opciones": [],
                "pondera": True,
                "puntaje_si": 20,
                "puntaje_no": 0,
                "condicion": None,
            },
        ]
    )


@pytest.mark.django_db
def test_reemplazar_preguntas_persiste_puntaje(encuesta):
    reemplazar_preguntas(encuesta, _payload_con_puntaje())

    unica = encuesta.preguntas.get(orden=1)
    si_no = encuesta.preguntas.get(orden=2)
    assert unica.pondera is True
    assert dict(unica.opciones.values_list("texto", "puntaje")) == {
        "Bueno": 10,
        "Malo": 0,
    }
    assert si_no.pondera is True
    assert si_no.puntaje_si == 20
    assert si_no.puntaje_no == 0


@pytest.mark.django_db
def test_serializar_preguntas_incluye_puntaje(encuesta):
    reemplazar_preguntas(encuesta, _payload_con_puntaje())

    serializado = serializar_preguntas(encuesta)

    assert serializado[0]["pondera"] is True
    assert serializado[0]["opciones"] == [
        {"texto": "Bueno", "puntaje": 10},
        {"texto": "Malo", "puntaje": 0},
    ]
    assert serializado[1]["puntaje_si"] == 20
    assert serializado[1]["puntaje_no"] == 0


@pytest.mark.django_db
def test_nueva_version_clona_puntaje(encuesta, usuario_creador):
    base = Pregunta.objects.create(
        encuesta=encuesta,
        texto="¿Cómo calificás?",
        tipo=TipoPregunta.OPCION_UNICA,
        orden=1,
        pondera=True,
    )
    base.opciones.create(texto="Bueno", valor="Bueno", orden=1, puntaje=10)
    base.opciones.create(texto="Malo", valor="Malo", orden=2, puntaje=0)
    si_no = Pregunta.objects.create(
        encuesta=encuesta,
        texto="¿Volverías?",
        tipo=TipoPregunta.SI_NO,
        orden=2,
        pondera=True,
        puntaje_si=20,
        puntaje_no=0,
    )
    actualizar_segmentacion(encuesta, tipo=TipoSegmentacion.TODOS_LOS_USUARIOS)
    ronda = publicar(encuesta, usuario=usuario_creador)
    cerrar_ronda(ronda)

    nueva = actualizar_encuesta(encuesta, usuario=usuario_creador)

    nueva_base = nueva.preguntas.get(texto=base.texto)
    nueva_si_no = nueva.preguntas.get(texto=si_no.texto)
    assert nueva_base.pondera is True
    assert dict(nueva_base.opciones.values_list("texto", "puntaje")) == {
        "Bueno": 10,
        "Malo": 0,
    }
    assert nueva_si_no.puntaje_si == 20
    assert nueva_si_no.puntaje_no == 0


# ---------------------------------------------------------------------------
# services_resultados: cálculo de puntaje
# ---------------------------------------------------------------------------


def _encuesta_ponderada(usuario_creador, respondientes, *, anonima=False):
    encuesta = crear_encuesta(
        usuario=usuario_creador,
        titulo="Evaluación",
        es_obligatoria=True,
        es_anonima=anonima,
        duracion_ronda_dias=7,
    )
    unica = Pregunta.objects.create(
        encuesta=encuesta,
        texto="¿Cómo calificás el servicio?",
        tipo=TipoPregunta.OPCION_UNICA,
        orden=1,
        pondera=True,
    )
    unica.opciones.create(texto="Bueno", valor="Bueno", orden=1, puntaje=10)
    unica.opciones.create(texto="Malo", valor="Malo", orden=2, puntaje=0)

    si_no = Pregunta.objects.create(
        encuesta=encuesta,
        texto="¿Volverías a usarlo?",
        tipo=TipoPregunta.SI_NO,
        orden=2,
        pondera=True,
        puntaje_si=20,
        puntaje_no=0,
    )

    multiple = Pregunta.objects.create(
        encuesta=encuesta,
        texto="¿Qué canales usás?",
        tipo=TipoPregunta.OPCION_MULTIPLE,
        orden=3,
        obligatoria=False,
        pondera=True,
    )
    multiple.opciones.create(texto="Web", valor="Web", orden=1, puntaje=5)
    multiple.opciones.create(texto="App", valor="App", orden=2, puntaje=5)

    escala = Pregunta.objects.create(
        encuesta=encuesta,
        texto="Puntuá del 1 al 10",
        tipo=TipoPregunta.ESCALA,
        orden=4,
        obligatoria=False,
        pondera=True,
    )

    # Condicional: solo se muestra si la pregunta única fue "Bueno". Pondera
    # igual, para probar que el total posible es fijo (regla de negocio
    # explícita) aunque a alguien no le haya aparecido.
    condicional = Pregunta.objects.create(
        encuesta=encuesta,
        texto="¿Por qué fue bueno?",
        tipo=TipoPregunta.SI_NO,
        orden=5,
        obligatoria=False,
        pondera=True,
        puntaje_si=15,
        puntaje_no=0,
        pregunta_condicion=unica,
        operador_condicion=OperadorCondicion.IGUAL,
        valor_condicion="Bueno",
    )

    actualizar_segmentacion(
        encuesta,
        tipo=TipoSegmentacion.LISTADO_DOCUMENTOS,
        destinatarios=[
            {"tipo_documento": TipoDocumento.DNI, "numero_documento": f"5000000{i}"}
            for i in range(3)
        ],
    )
    ronda = publicar(encuesta, usuario=usuario_creador)
    return encuesta, ronda, unica, si_no, multiple, escala, condicional


@pytest.mark.django_db
def test_puntaje_total_posible_suma_maximos_por_pregunta(
    usuario_creador, respondientes
):
    encuesta, *_ = _encuesta_ponderada(usuario_creador, respondientes)
    # unica: max(10, 0)=10 | si_no: max(20,0)=20 | multiple: 5+5=10
    # escala: 10 (fijo) | condicional (si_no): max(15,0)=15
    assert puntaje_total_posible(encuesta) == 10 + 20 + 10 + 10 + 15


@pytest.mark.django_db
def test_encuesta_pondera_false_sin_preguntas_ponderadas(usuario_creador):
    encuesta = crear_encuesta(
        usuario=usuario_creador,
        titulo="Sin puntaje",
        es_obligatoria=True,
        duracion_ronda_dias=7,
    )
    Pregunta.objects.create(
        encuesta=encuesta, texto="¿Todo bien?", tipo=TipoPregunta.SI_NO
    )
    assert encuesta_pondera(encuesta) is False


@pytest.mark.django_db
def test_get_puntajes_ronda_vacio_si_no_pondera(usuario_creador, respondientes):
    encuesta = crear_encuesta(
        usuario=usuario_creador,
        titulo="Sin puntaje",
        es_obligatoria=True,
        duracion_ronda_dias=7,
    )
    pregunta = Pregunta.objects.create(
        encuesta=encuesta, texto="¿Todo bien?", tipo=TipoPregunta.SI_NO
    )
    actualizar_segmentacion(encuesta, tipo=TipoSegmentacion.TODOS_LOS_USUARIOS)
    ronda = publicar(encuesta, usuario=usuario_creador)
    registrar_respuesta(ronda, respondientes[0], {f"respuesta-{pregunta.pk}": "si"})

    assert get_puntajes_ronda(ronda) == []


@pytest.mark.django_db
def test_get_puntajes_ronda_calcula_obtenido_y_total_fijo(
    usuario_creador, respondientes
):
    """El total posible es fijo: a respondientes[0] no le aparece la
    pregunta condicional (contestó 'Malo'), pero sus 15 puntos posibles
    igual cuentan para el total (decisión de negocio explícita)."""
    encuesta, ronda, unica, si_no, multiple, escala, condicional = _encuesta_ponderada(
        usuario_creador, respondientes
    )
    total_esperado = puntaje_total_posible(encuesta)

    registrar_respuesta(
        ronda,
        respondientes[0],
        MultiValueDict(
            {
                f"respuesta-{unica.pk}": ["Malo"],
                f"respuesta-{si_no.pk}": ["si"],
                f"respuesta-{multiple.pk}": ["Web", "App"],
                f"respuesta-{escala.pk}": ["7"],
            }
        ),
    )

    puntajes = get_puntajes_ronda(ronda)
    assert len(puntajes) == 1
    puntaje = puntajes[0]
    # unica "Malo"=0 + si_no "si"=20 + multiple Web+App=10 + escala=7
    # + condicional (no visible, no respondida)=0
    assert puntaje.obtenido == 0 + 20 + 10 + 7 + 0
    assert puntaje.total_posible == total_esperado
    assert puntaje.porcentaje == round(puntaje.obtenido * 100 / total_esperado, 1)


@pytest.mark.django_db
def test_get_puntajes_ronda_ordena_de_mayor_a_menor(usuario_creador, respondientes):
    encuesta, ronda, unica, si_no, multiple, escala, condicional = _encuesta_ponderada(
        usuario_creador, respondientes
    )
    registrar_respuesta(
        ronda,
        respondientes[0],
        MultiValueDict(
            {f"respuesta-{unica.pk}": ["Malo"], f"respuesta-{si_no.pk}": ["no"]}
        ),
    )
    registrar_respuesta(
        ronda,
        respondientes[1],
        MultiValueDict(
            {f"respuesta-{unica.pk}": ["Bueno"], f"respuesta-{si_no.pk}": ["si"]}
        ),
    )

    puntajes = get_puntajes_ronda(ronda)
    assert puntajes[0].obtenido >= puntajes[1].obtenido
    assert puntajes[0].obtenido == 10 + 20  # Bueno + Sí


@pytest.mark.django_db
def test_get_puntajes_ronda_oculta_usuario_si_es_anonima(
    usuario_creador, respondientes
):
    encuesta, ronda, unica, si_no, multiple, escala, condicional = _encuesta_ponderada(
        usuario_creador, respondientes, anonima=True
    )
    registrar_respuesta(
        ronda,
        respondientes[0],
        MultiValueDict(
            {f"respuesta-{unica.pk}": ["Bueno"], f"respuesta-{si_no.pk}": ["si"]}
        ),
    )

    puntajes = get_puntajes_ronda(ronda)
    assert puntajes[0].usuario is None


@pytest.mark.django_db
def test_get_puntajes_ronda_muestra_usuario_si_no_es_anonima(
    usuario_creador, respondientes
):
    encuesta, ronda, unica, si_no, multiple, escala, condicional = _encuesta_ponderada(
        usuario_creador, respondientes, anonima=False
    )
    registrar_respuesta(
        ronda,
        respondientes[0],
        MultiValueDict(
            {f"respuesta-{unica.pk}": ["Bueno"], f"respuesta-{si_no.pk}": ["si"]}
        ),
    )

    puntajes = get_puntajes_ronda(ronda)
    assert puntajes[0].usuario == respondientes[0].username


# ---------------------------------------------------------------------------
# Exportación
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_export_incluye_columnas_de_puntaje_si_encuesta_pondera(
    usuario_creador, respondientes
):
    encuesta, ronda, unica, si_no, multiple, escala, condicional = _encuesta_ponderada(
        usuario_creador, respondientes
    )
    registrar_respuesta(
        ronda,
        respondientes[0],
        MultiValueDict(
            {f"respuesta-{unica.pk}": ["Bueno"], f"respuesta-{si_no.pk}": ["si"]}
        ),
    )

    preguntas, filas = build_export_rows(ronda)
    headers = build_export_headers(encuesta, preguntas)

    assert "Puntaje obtenido" in headers
    assert "Puntaje total" in headers
    indice_obtenido = headers.index("Puntaje obtenido")
    indice_total = headers.index("Puntaje total")
    assert filas[0][indice_obtenido] == 10 + 20
    assert filas[0][indice_total] == puntaje_total_posible(encuesta)


@pytest.mark.django_db
def test_export_no_incluye_columnas_de_puntaje_si_no_pondera(
    usuario_creador, respondientes
):
    encuesta = crear_encuesta(
        usuario=usuario_creador,
        titulo="Sin puntaje",
        es_obligatoria=True,
        duracion_ronda_dias=7,
    )
    pregunta = Pregunta.objects.create(
        encuesta=encuesta, texto="¿Todo bien?", tipo=TipoPregunta.SI_NO
    )
    actualizar_segmentacion(encuesta, tipo=TipoSegmentacion.TODOS_LOS_USUARIOS)
    ronda = publicar(encuesta, usuario=usuario_creador)
    registrar_respuesta(ronda, respondientes[0], {f"respuesta-{pregunta.pk}": "si"})

    preguntas, filas = build_export_rows(ronda)
    headers = build_export_headers(encuesta, preguntas)

    assert "Puntaje obtenido" not in headers
    assert "Puntaje total" not in headers


# ---------------------------------------------------------------------------
# Vista de resultados
# ---------------------------------------------------------------------------


def _permisos_resultados(django_user_model):
    from django.contrib.auth.models import Permission

    user = django_user_model.objects.create_user(username="ve-puntajes", password="x")
    user.user_permissions.add(
        *Permission.objects.filter(
            content_type__app_label="encuestas",
            codename__in=["view_encuesta", "ver_resultados"],
        )
    )
    return user


@pytest.mark.django_db
def test_vista_resultados_muestra_seccion_de_puntaje(
    client, django_user_model, usuario_creador, respondientes
):
    encuesta, ronda, unica, si_no, multiple, escala, condicional = _encuesta_ponderada(
        usuario_creador, respondientes
    )
    registrar_respuesta(
        ronda,
        respondientes[0],
        MultiValueDict(
            {f"respuesta-{unica.pk}": ["Bueno"], f"respuesta-{si_no.pk}": ["si"]}
        ),
    )
    user = _permisos_resultados(django_user_model)
    client.force_login(user)

    response = client.get(reverse("encuestas_resultados", args=[encuesta.pk]))

    assert response.status_code == 200
    assert b"Puntaje por respuesta" in response.content


@pytest.mark.django_db
def test_vista_resultados_no_muestra_seccion_de_puntaje_sin_pondera(
    client, django_user_model, usuario_creador, respondientes
):
    # LISTADO_DOCUMENTOS (no TODOS_LOS_USUARIOS): si el usuario que consulta
    # resultados no tiene DNI cargado, TODOS_LOS_USUARIOS + es_obligatoria lo
    # segmentaría también a él y EncuestaObligatoriaMiddleware lo bloquearía
    # antes de llegar a la vista (mismo problema ya resuelto en otras suites
    # de encuestas).
    encuesta = crear_encuesta(
        usuario=usuario_creador,
        titulo="Sin puntaje",
        es_obligatoria=True,
        duracion_ronda_dias=7,
    )
    Pregunta.objects.create(
        encuesta=encuesta, texto="¿Todo bien?", tipo=TipoPregunta.SI_NO
    )
    actualizar_segmentacion(
        encuesta,
        tipo=TipoSegmentacion.LISTADO_DOCUMENTOS,
        destinatarios=[
            {"tipo_documento": TipoDocumento.DNI, "numero_documento": "50000009"}
        ],
    )
    publicar(encuesta, usuario=usuario_creador)
    user = _permisos_resultados(django_user_model)
    client.force_login(user)

    response = client.get(reverse("encuestas_resultados", args=[encuesta.pk]))

    assert response.status_code == 200
    assert b"Puntaje por respuesta" not in response.content
