from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.datastructures import MultiValueDict

from encuestas.models import (
    CumplimientoRonda,
    Encuesta,
    EstadoRonda,
    OperadorCondicion,
    OpcionPregunta,
    Pregunta,
    RecordatorioUsuario,
    RespuestaPregunta,
    RespuestaRonda,
    RondaEncuesta,
    TipoDocumento,
    TipoPregunta,
    TipoSegmentacion,
)
from encuestas.services import (
    actualizar_segmentacion,
    crear_encuesta,
    get_rondas_pendientes,
    posponer_ronda,
    publicar,
    registrar_respuesta,
    usuario_esta_segmentado,
)


@pytest.fixture
def usuario_creador(django_user_model):
    return django_user_model.objects.create_user(username="creador", password="x")


@pytest.fixture
def respondiente(django_user_model):
    user = django_user_model.objects.create_user(username="respondiente", password="x")
    user.profile.dni = "30111222"
    user.profile.cuil = "20301112223"
    user.profile.save()
    return user


def _publicar_con_pregunta_si_no(
    usuario_creador,
    *,
    obligatoria=True,
    tipo_segmentacion=TipoSegmentacion.TODOS_LOS_USUARIOS,
    destinatarios=None,
):
    encuesta = crear_encuesta(
        usuario=usuario_creador,
        titulo="Satisfacción",
        es_obligatoria=obligatoria,
        intervalo_recordatorio_dias=None if obligatoria else 3,
        duracion_ronda_dias=7,
    )
    Pregunta.objects.create(
        encuesta=encuesta, texto="¿Todo bien?", tipo=TipoPregunta.SI_NO, orden=1
    )
    actualizar_segmentacion(
        encuesta, tipo=tipo_segmentacion, destinatarios=destinatarios
    )
    ronda = publicar(encuesta, usuario=usuario_creador)
    return encuesta, ronda


@pytest.mark.django_db
def test_usuario_esta_segmentado_todos_los_usuarios(usuario_creador, respondiente):
    encuesta, _ = _publicar_con_pregunta_si_no(usuario_creador)
    assert usuario_esta_segmentado(encuesta, respondiente)


@pytest.mark.django_db
def test_creador_esta_segmentado_por_su_propia_encuesta(usuario_creador):
    encuesta, _ = _publicar_con_pregunta_si_no(usuario_creador)
    assert usuario_esta_segmentado(encuesta, usuario_creador)


@pytest.mark.django_db
def test_usuario_esta_segmentado_por_dni(usuario_creador, respondiente):
    encuesta, _ = _publicar_con_pregunta_si_no(
        usuario_creador,
        tipo_segmentacion=TipoSegmentacion.LISTADO_DOCUMENTOS,
        destinatarios=[
            {"tipo_documento": TipoDocumento.DNI, "numero_documento": "30111222"}
        ],
    )
    assert usuario_esta_segmentado(encuesta, respondiente)


@pytest.mark.django_db
def test_usuario_no_segmentado_por_dni_ajeno(usuario_creador, respondiente):
    encuesta, _ = _publicar_con_pregunta_si_no(
        usuario_creador,
        tipo_segmentacion=TipoSegmentacion.LISTADO_DOCUMENTOS,
        destinatarios=[
            {"tipo_documento": TipoDocumento.DNI, "numero_documento": "99999999"}
        ],
    )
    assert not usuario_esta_segmentado(encuesta, respondiente)


@pytest.mark.django_db
def test_usuario_esta_segmentado_por_cuit_equivalente_a_su_cuil(
    usuario_creador, respondiente
):
    encuesta, _ = _publicar_con_pregunta_si_no(
        usuario_creador,
        tipo_segmentacion=TipoSegmentacion.LISTADO_DOCUMENTOS,
        destinatarios=[
            {"tipo_documento": TipoDocumento.CUIT, "numero_documento": "20301112223"}
        ],
    )
    assert usuario_esta_segmentado(encuesta, respondiente)


@pytest.mark.django_db
def test_get_rondas_pendientes_excluye_ronda_vencida_aun_sin_worker(
    usuario_creador, respondiente
):
    _, ronda = _publicar_con_pregunta_si_no(usuario_creador)
    ronda.fecha_cierre_programada = timezone.now() - timedelta(seconds=1)
    ronda.save(update_fields=["fecha_cierre_programada"])

    assert get_rondas_pendientes(respondiente) == []


@pytest.mark.django_db
def test_get_rondas_pendientes_ordena_por_fecha_de_cierre_mas_proxima(
    usuario_creador, respondiente
):
    _, ronda_lejana = _publicar_con_pregunta_si_no(usuario_creador)
    ronda_lejana.fecha_cierre_programada = timezone.now() + timedelta(days=10)
    ronda_lejana.save(update_fields=["fecha_cierre_programada"])

    _, ronda_cercana = _publicar_con_pregunta_si_no(usuario_creador)
    ronda_cercana.fecha_cierre_programada = timezone.now() + timedelta(days=1)
    ronda_cercana.save(update_fields=["fecha_cierre_programada"])

    pendientes = get_rondas_pendientes(respondiente)

    assert [r.pk for r in pendientes] == [ronda_cercana.pk, ronda_lejana.pk]


@pytest.mark.django_db
def test_get_rondas_pendientes_excluye_ya_respondida(usuario_creador, respondiente):
    _, ronda = _publicar_con_pregunta_si_no(usuario_creador)
    CumplimientoRonda.objects.create(ronda=ronda, usuario=respondiente)

    assert get_rondas_pendientes(respondiente) == []


@pytest.mark.django_db
def test_get_rondas_pendientes_excluye_snoozeada(usuario_creador, respondiente):
    _, ronda = _publicar_con_pregunta_si_no(usuario_creador, obligatoria=False)
    posponer_ronda(ronda, respondiente)

    assert get_rondas_pendientes(respondiente) == []


@pytest.mark.django_db
def test_get_rondas_pendientes_reaparece_pasada_la_fecha_de_snooze(
    usuario_creador, respondiente
):
    _, ronda = _publicar_con_pregunta_si_no(usuario_creador, obligatoria=False)
    RecordatorioUsuario.objects.create(
        ronda=ronda,
        usuario=respondiente,
        fecha_proximo_aviso=timezone.now() - timedelta(minutes=1),
    )

    assert get_rondas_pendientes(respondiente) == [ronda]


@pytest.mark.django_db
def test_registrar_respuesta_guarda_valor_y_marca_completa(
    usuario_creador, respondiente
):
    _, ronda = _publicar_con_pregunta_si_no(usuario_creador)
    pregunta = ronda.encuesta.preguntas.get()

    respuesta_ronda = registrar_respuesta(
        ronda, respondiente, {f"respuesta-{pregunta.pk}": "si"}
    )

    assert respuesta_ronda.completa is True
    assert respuesta_ronda.usuario == respondiente
    detalle = respuesta_ronda.respuestas_pregunta.get()
    assert detalle.valor_texto == "si"


@pytest.mark.django_db
def test_registrar_respuesta_opcion_unica_y_multiple(usuario_creador, respondiente):
    encuesta = crear_encuesta(
        usuario=usuario_creador,
        titulo="Con opciones",
        es_obligatoria=True,
        duracion_ronda_dias=7,
    )
    unica = Pregunta.objects.create(
        encuesta=encuesta, texto="Única", tipo=TipoPregunta.OPCION_UNICA, orden=1
    )
    op1 = OpcionPregunta.objects.create(pregunta=unica, texto="A", valor="A", orden=1)
    OpcionPregunta.objects.create(pregunta=unica, texto="B", valor="B", orden=2)
    multiple = Pregunta.objects.create(
        encuesta=encuesta,
        texto="Múltiple",
        tipo=TipoPregunta.OPCION_MULTIPLE,
        obligatoria=False,
        orden=2,
    )
    opm1 = OpcionPregunta.objects.create(
        pregunta=multiple, texto="X", valor="X", orden=1
    )
    opm2 = OpcionPregunta.objects.create(
        pregunta=multiple, texto="Y", valor="Y", orden=2
    )
    actualizar_segmentacion(encuesta, tipo=TipoSegmentacion.TODOS_LOS_USUARIOS)
    ronda = publicar(encuesta, usuario=usuario_creador)

    respuesta_ronda = registrar_respuesta(
        ronda,
        respondiente,
        MultiValueDict(
            {f"respuesta-{unica.pk}": ["A"], f"respuesta-{multiple.pk}": ["X", "Y"]}
        ),
    )

    resp_unica = respuesta_ronda.respuestas_pregunta.get(pregunta=unica)
    resp_multiple = respuesta_ronda.respuestas_pregunta.get(pregunta=multiple)
    assert list(resp_unica.opciones_seleccionadas.all()) == [op1]
    assert set(resp_multiple.opciones_seleccionadas.all()) == {opm1, opm2}


@pytest.mark.django_db
def test_registrar_respuesta_pregunta_obligatoria_faltante_no_deja_residuo(
    usuario_creador, respondiente
):
    _, ronda = _publicar_con_pregunta_si_no(usuario_creador)

    with pytest.raises(ValidationError):
        registrar_respuesta(ronda, respondiente, {})

    assert not RespuestaRonda.objects.filter(ronda=ronda).exists()
    assert not CumplimientoRonda.objects.filter(
        ronda=ronda, usuario=respondiente
    ).exists()
    assert not RespuestaPregunta.objects.exists()


@pytest.mark.django_db
def test_registrar_respuesta_pregunta_condicional_no_visible_se_omite(
    usuario_creador, respondiente
):
    encuesta = crear_encuesta(
        usuario=usuario_creador,
        titulo="Con condición",
        es_obligatoria=True,
        duracion_ronda_dias=7,
    )
    base = Pregunta.objects.create(
        encuesta=encuesta, texto="¿Usás X?", tipo=TipoPregunta.SI_NO, orden=1
    )
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
    ronda = publicar(encuesta, usuario=usuario_creador)

    # Responde "no" a la base: la dependiente no debe exigirse ni guardarse,
    # aunque esté marcada obligatoria en el modelo.
    dependiente.obligatoria = True
    dependiente.save(update_fields=["obligatoria"])

    respuesta_ronda = registrar_respuesta(
        ronda, respondiente, {f"respuesta-{base.pk}": "no"}
    )

    assert respuesta_ronda.respuestas_pregunta.filter(pregunta=dependiente).count() == 0


@pytest.mark.django_db
def test_registrar_respuesta_duplicada_falla(usuario_creador, respondiente):
    _, ronda = _publicar_con_pregunta_si_no(usuario_creador)
    pregunta = ronda.encuesta.preguntas.get()
    registrar_respuesta(ronda, respondiente, {f"respuesta-{pregunta.pk}": "si"})

    with pytest.raises(ValidationError):
        registrar_respuesta(ronda, respondiente, {f"respuesta-{pregunta.pk}": "no"})


@pytest.mark.django_db
def test_respuesta_anonima_no_enlaza_el_contenido_con_el_usuario(
    usuario_creador, respondiente
):
    encuesta, ronda = _publicar_con_pregunta_si_no(usuario_creador)
    encuesta.es_anonima = True
    encuesta.save(update_fields=["es_anonima"])
    pregunta = encuesta.preguntas.get()

    respuesta = registrar_respuesta(
        ronda, respondiente, {f"respuesta-{pregunta.pk}": "si"}
    )

    assert respuesta.usuario is None
    assert CumplimientoRonda.objects.filter(ronda=ronda, usuario=respondiente).exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "valor",
    ["inexistente", "", "si-no-valido"],
)
def test_respuesta_si_no_invalida_no_se_guarda(usuario_creador, respondiente, valor):
    _, ronda = _publicar_con_pregunta_si_no(usuario_creador)
    pregunta = ronda.encuesta.preguntas.get()

    with pytest.raises(ValidationError):
        registrar_respuesta(ronda, respondiente, {f"respuesta-{pregunta.pk}": valor})

    assert not RespuestaRonda.objects.filter(ronda=ronda).exists()
    assert not CumplimientoRonda.objects.filter(
        ronda=ronda, usuario=respondiente
    ).exists()


@pytest.mark.django_db
def test_opcion_inexistente_no_marca_la_respuesta_como_completa(
    usuario_creador, respondiente
):
    encuesta = crear_encuesta(
        usuario=usuario_creador,
        titulo="Opciones válidas",
        es_obligatoria=True,
        duracion_ronda_dias=7,
    )
    pregunta = Pregunta.objects.create(
        encuesta=encuesta, texto="Elegí", tipo=TipoPregunta.OPCION_UNICA, orden=1
    )
    OpcionPregunta.objects.create(pregunta=pregunta, texto="A", valor="A")
    OpcionPregunta.objects.create(pregunta=pregunta, texto="B", valor="B")
    actualizar_segmentacion(encuesta, tipo=TipoSegmentacion.TODOS_LOS_USUARIOS)
    ronda = publicar(encuesta, usuario=usuario_creador)

    with pytest.raises(ValidationError):
        registrar_respuesta(ronda, respondiente, {f"respuesta-{pregunta.pk}": "X"})

    assert not RespuestaRonda.objects.filter(ronda=ronda).exists()
    assert not CumplimientoRonda.objects.filter(
        ronda=ronda, usuario=respondiente
    ).exists()


@pytest.mark.django_db
def test_escala_fuera_de_rango_no_se_guarda(usuario_creador, respondiente):
    encuesta = crear_encuesta(
        usuario=usuario_creador,
        titulo="Escala válida",
        es_obligatoria=True,
        duracion_ronda_dias=7,
    )
    pregunta = Pregunta.objects.create(
        encuesta=encuesta, texto="Puntuá", tipo=TipoPregunta.ESCALA, orden=1
    )
    actualizar_segmentacion(encuesta, tipo=TipoSegmentacion.TODOS_LOS_USUARIOS)
    ronda = publicar(encuesta, usuario=usuario_creador)

    with pytest.raises(ValidationError):
        registrar_respuesta(ronda, respondiente, {f"respuesta-{pregunta.pk}": "11"})

    assert not RespuestaRonda.objects.filter(ronda=ronda).exists()


@pytest.mark.django_db
def test_registrar_respuesta_ronda_cerrada_falla(usuario_creador, respondiente):
    _, ronda = _publicar_con_pregunta_si_no(usuario_creador)
    ronda.estado = EstadoRonda.CERRADA
    ronda.save(update_fields=["estado"])

    with pytest.raises(ValidationError):
        registrar_respuesta(ronda, respondiente, {})


@pytest.mark.django_db
def test_registrar_respuesta_ronda_vencida_falla_aun_sin_worker(
    usuario_creador, respondiente
):
    _, ronda = _publicar_con_pregunta_si_no(usuario_creador)
    pregunta = ronda.encuesta.preguntas.get()
    ronda.fecha_cierre_programada = timezone.now() - timedelta(seconds=1)
    ronda.save(update_fields=["fecha_cierre_programada"])

    with pytest.raises(ValidationError):
        registrar_respuesta(ronda, respondiente, {f"respuesta-{pregunta.pk}": "si"})

    assert not RespuestaRonda.objects.filter(ronda=ronda).exists()


@pytest.mark.django_db
def test_registrar_respuesta_usuario_no_segmentado_falla(usuario_creador, respondiente):
    _, ronda = _publicar_con_pregunta_si_no(
        usuario_creador,
        tipo_segmentacion=TipoSegmentacion.LISTADO_DOCUMENTOS,
        destinatarios=[{"tipo_documento": TipoDocumento.DNI, "numero_documento": "1"}],
    )

    with pytest.raises(ValidationError):
        registrar_respuesta(ronda, respondiente, {})


@pytest.mark.django_db
def test_registrar_respuesta_borra_el_recordatorio_pendiente(
    usuario_creador, respondiente
):
    _, ronda = _publicar_con_pregunta_si_no(usuario_creador, obligatoria=False)
    posponer_ronda(ronda, respondiente)
    pregunta = ronda.encuesta.preguntas.get()

    registrar_respuesta(ronda, respondiente, {f"respuesta-{pregunta.pk}": "si"})

    assert not RecordatorioUsuario.objects.filter(
        ronda=ronda, usuario=respondiente
    ).exists()


@pytest.mark.django_db
def test_posponer_ronda_crea_recordatorio_segun_intervalo(
    usuario_creador, respondiente
):
    encuesta, ronda = _publicar_con_pregunta_si_no(usuario_creador, obligatoria=False)
    encuesta.intervalo_recordatorio_dias = 5
    encuesta.save(update_fields=["intervalo_recordatorio_dias"])

    antes = timezone.now()
    recordatorio = posponer_ronda(ronda, respondiente)

    assert recordatorio.fecha_proximo_aviso >= antes + timedelta(days=5)


@pytest.mark.django_db
def test_posponer_ronda_actualiza_si_ya_existe(usuario_creador, respondiente):
    _, ronda = _publicar_con_pregunta_si_no(usuario_creador, obligatoria=False)
    primero = posponer_ronda(ronda, respondiente)
    segundo = posponer_ronda(ronda, respondiente)

    assert primero.pk == segundo.pk
    assert (
        RecordatorioUsuario.objects.filter(ronda=ronda, usuario=respondiente).count()
        == 1
    )


@pytest.mark.django_db
def test_posponer_ronda_obligatoria_falla(usuario_creador, respondiente):
    _, ronda = _publicar_con_pregunta_si_no(usuario_creador, obligatoria=True)

    with pytest.raises(ValidationError):
        posponer_ronda(ronda, respondiente)
