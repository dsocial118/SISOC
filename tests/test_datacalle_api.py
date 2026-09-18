"""Tests de la API que consume la app DataCalle (contrato D2.5)."""

import datetime
import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from core.models import Provincia
from datacalle.models import Encuesta, Relevamiento
from datacalle.services import cerrar_relevamiento
from users.models import RelevadorCalleProvincia


@pytest.fixture
def provincia(db):
    return Provincia.objects.create(nombre="Córdoba")


def _entrevistador(provincia, username="entrev_api"):
    user = get_user_model().objects.create_user(
        username=username, email=f"{username}@example.com", password="Sisoc12345!"
    )
    user.profile.es_relevador_calle = True
    user.profile.datacalle_rol = "entrevistador"
    user.profile.save()
    RelevadorCalleProvincia.objects.create(profile=user.profile, provincia=provincia)
    return user


def _cliente(user):
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


def _relevamiento(provincia, equipo=(), **extra):
    datos = {
        "denominacion": "Operativo invierno",
        "provincia": provincia,
        "fase": Relevamiento.Fase.ESPACIO_PUBLICO,
        "area_operativa": "Plaza San Martín",
        "fecha_inicio": datetime.date(2026, 9, 15),
        "fecha_fin": datetime.date(2026, 9, 19),
    }
    datos.update(extra)
    relevamiento = Relevamiento.objects.create(**datos)
    for integrante in equipo:
        relevamiento.equipo.add(integrante)
    return relevamiento


RESPUESTAS = {
    "grupoId": "11111111-1111-4111-8111-111111111111",
    "esCabeceraGrupo": "si",
    "personaEntrevistada": "r19a59_varon",
    "personasObservadas": 3,
    "realizaEntrevista": "si",
    "codigoEntrevistado": "LURO15031980",
    "lugarHallazgo": "espacioPublico",
    "ubicacionGrupo": {"lat": -31.420083, "lon": -64.188776, "precision": 8},
}


def _cuerpo(relevamiento, **extra):
    datos = {
        "relevamiento_id": str(relevamiento.id),
        "variante": "completo",
        "estado": "completa",
        "fecha_inicio": "2026-09-16T00:40:00Z",
        "fecha_hora_fin": "2026-09-16T00:52:30Z",
        "respuestas": RESPUESTAS,
    }
    datos.update(extra)
    return datos


@pytest.mark.django_db
def test_solo_veo_las_tareas_donde_estoy_en_el_equipo(provincia):
    mio = _entrevistador(provincia, "entrev_mio")
    otro = _entrevistador(provincia, "entrev_otro")
    _relevamiento(provincia, equipo=[mio], denominacion="Mi operativo")
    _relevamiento(provincia, equipo=[otro], denominacion="De otro")

    respuesta = _cliente(mio).get("/api/datacalle/relevamientos/")

    assert respuesta.status_code == 200
    nombres = [r["denominacion"] for r in respuesta.data["results"]]
    assert nombres == ["Mi operativo"]


@pytest.mark.django_db
def test_la_tarea_trae_el_shape_acordado(provincia):
    entrevistador = _entrevistador(provincia)
    relevamiento = _relevamiento(provincia, equipo=[entrevistador])

    respuesta = _cliente(entrevistador).get(
        f"/api/datacalle/relevamientos/{relevamiento.id}/"
    )

    assert respuesta.status_code == 200
    datos = respuesta.data
    assert datos["provincia"] == {"id": provincia.id, "nombre": "Córdoba"}
    assert datos["fase"] == "espacio_publico"
    assert datos["area_operativa"] == "Plaza San Martín"
    assert datos["dispositivo"] is None
    assert datos["estado"] == "planificado"
    assert datos["cantidad_encuestas"] == 0
    assert datos["equipo"][0]["id"] == entrevistador.id
    assert "actualizado_en" in datos


@pytest.mark.django_db
def test_sin_rol_datacalle_no_entra_a_la_api(provincia):
    ajeno = get_user_model().objects.create_user(
        username="sin_rol", email="sin_rol@example.com", password="Sisoc12345!"
    )

    respuesta = _cliente(ajeno).get("/api/datacalle/relevamientos/")

    assert respuesta.status_code == 403


@pytest.mark.django_db
def test_alta_de_caso_es_idempotente_por_uuid(provincia):
    entrevistador = _entrevistador(provincia)
    relevamiento = _relevamiento(provincia, equipo=[entrevistador])
    client = _cliente(entrevistador)
    caso_id = str(uuid.uuid4())

    primera = client.put(
        f"/api/datacalle/encuestas/{caso_id}/", _cuerpo(relevamiento), format="json"
    )
    segunda = client.put(
        f"/api/datacalle/encuestas/{caso_id}/", _cuerpo(relevamiento), format="json"
    )

    assert primera.status_code == 201
    assert segunda.status_code == 200
    assert Encuesta.objects.filter(relevamiento=relevamiento).count() == 1


@pytest.mark.django_db
def test_el_caso_copia_las_columnas_indexadas(provincia):
    entrevistador = _entrevistador(provincia)
    relevamiento = _relevamiento(provincia, equipo=[entrevistador])
    caso_id = str(uuid.uuid4())

    _cliente(entrevistador).put(
        f"/api/datacalle/encuestas/{caso_id}/", _cuerpo(relevamiento), format="json"
    )

    caso = Encuesta.objects.get(pk=caso_id)
    assert caso.grupo_id == RESPUESTAS["grupoId"]
    assert caso.es_cabecera_grupo is True
    assert caso.persona_entrevistada == "r19a59_varon"
    assert caso.personas_observadas == 3
    assert caso.realiza_entrevista == "si"
    assert caso.codigo_entrevistado == "LURO15031980"
    assert caso.lugar_hallazgo == "espacioPublico"
    assert caso.lat == pytest.approx(-31.420083)
    assert caso.relevador == entrevistador
    assert caso.origen == Encuesta.Origen.APP


@pytest.mark.django_db
def test_el_primer_caso_pone_el_operativo_en_curso(provincia):
    entrevistador = _entrevistador(provincia)
    relevamiento = _relevamiento(provincia, equipo=[entrevistador])

    _cliente(entrevistador).put(
        f"/api/datacalle/encuestas/{uuid.uuid4()}/",
        _cuerpo(relevamiento),
        format="json",
    )

    relevamiento.refresh_from_db()
    assert relevamiento.estado == Relevamiento.Estado.EN_CURSO


@pytest.mark.django_db
def test_no_puedo_cargar_casos_en_un_operativo_ajeno(provincia):
    mio = _entrevistador(provincia, "entrev_a")
    otro = _entrevistador(provincia, "entrev_b")
    ajeno = _relevamiento(provincia, equipo=[otro])

    respuesta = _cliente(mio).put(
        f"/api/datacalle/encuestas/{uuid.uuid4()}/", _cuerpo(ajeno), format="json"
    )

    assert respuesta.status_code == 404
    assert Encuesta.objects.count() == 0


@pytest.mark.django_db
def test_operativo_cerrado_rechaza_casos_con_409(provincia):
    entrevistador = _entrevistador(provincia)
    relevamiento = _relevamiento(
        provincia, equipo=[entrevistador], estado=Relevamiento.Estado.FINALIZADO
    )

    respuesta = _cliente(entrevistador).put(
        f"/api/datacalle/encuestas/{uuid.uuid4()}/",
        _cuerpo(relevamiento),
        format="json",
    )

    assert respuesta.status_code == 409
    assert respuesta.data["codigo"] == "relevamiento_cerrado"


@pytest.mark.django_db
def test_cierre_guarda_los_datos_de_campo(provincia):
    """Los datos de campo del cierre se guardan tal como llegan.

    QA-0020 le sacó el cierre a la app, así que esto ya no se ejerce por la
    API: se prueba contra el servicio, que es lo que usa el backoffice.
    """
    coordinador = _entrevistador(provincia, "coord_cierre")
    relevamiento = _relevamiento(provincia, equipo=[coordinador])

    cerrar_relevamiento(
        relevamiento=relevamiento,
        user=coordinador,
        datos={
            "fecha_cierre": datetime.datetime(
                2026, 9, 19, 23, 45, tzinfo=datetime.timezone.utc
            ),
            "lat": -31.416668,
            "lon": -64.183334,
            "observacion_asentamiento": ["consumoProblematico", "mueblesEnseres"],
            "otra_observacion": None,
        },
    )

    relevamiento.refresh_from_db()
    assert relevamiento.estado == Relevamiento.Estado.FINALIZADO
    assert relevamiento.cerrado_por == coordinador
    assert relevamiento.lat == pytest.approx(-31.416668)
    assert relevamiento.observacion_asentamiento == [
        "consumoProblematico",
        "mueblesEnseres",
    ]


@pytest.mark.django_db
def test_cerrar_dos_veces_no_es_error(provincia):
    """La idempotencia sigue importando: el backoffice puede reintentar."""
    coordinador = _entrevistador(provincia, "coord_idem")
    relevamiento = _relevamiento(provincia, equipo=[coordinador])

    _, primera = cerrar_relevamiento(relevamiento=relevamiento, user=coordinador)
    _, segunda = cerrar_relevamiento(relevamiento=relevamiento, user=coordinador)

    assert primera is True
    assert segunda is False


@pytest.mark.django_db
def test_puedo_recuperar_los_casos_del_operativo(provincia):
    entrevistador = _entrevistador(provincia)
    relevamiento = _relevamiento(provincia, equipo=[entrevistador])
    client = _cliente(entrevistador)
    client.put(
        f"/api/datacalle/encuestas/{uuid.uuid4()}/",
        _cuerpo(relevamiento),
        format="json",
    )

    respuesta = client.get(f"/api/datacalle/relevamientos/{relevamiento.id}/encuestas/")

    assert respuesta.status_code == 200
    assert respuesta.data["count"] == 1
    assert respuesta.data["results"][0]["respuestas"]["codigoEntrevistado"] == (
        "LURO15031980"
    )


@pytest.mark.django_db
def test_filtro_desde_trae_solo_lo_que_cambio(provincia):
    entrevistador = _entrevistador(provincia)
    _relevamiento(provincia, equipo=[entrevistador])

    futuro = "2030-01-01T00:00:00Z"
    respuesta = _cliente(entrevistador).get(
        f"/api/datacalle/relevamientos/?desde={futuro}"
    )

    assert respuesta.status_code == 200
    assert respuesta.data["count"] == 0


@pytest.mark.django_db
def test_baja_de_caso_es_logica(provincia):
    entrevistador = _entrevistador(provincia)
    relevamiento = _relevamiento(provincia, equipo=[entrevistador])
    client = _cliente(entrevistador)
    caso_id = str(uuid.uuid4())
    client.put(
        f"/api/datacalle/encuestas/{caso_id}/", _cuerpo(relevamiento), format="json"
    )

    respuesta = client.delete(f"/api/datacalle/encuestas/{caso_id}/")

    assert respuesta.status_code == 204
    assert Encuesta.objects.filter(pk=caso_id).exists() is False
    assert Encuesta.all_objects.filter(pk=caso_id).exists() is True


@pytest.mark.django_db
def test_catalogos_sirven_el_instrumento_vigente(provincia):
    entrevistador = _entrevistador(provincia)

    respuesta = _cliente(entrevistador).get("/api/datacalle/catalogos/")

    assert respuesta.status_code == 200
    # Pinneada a propósito: al sincronizar `datacalle/instrumento/` con el
    # contrato hay que subirla acá, así la copia no queda vieja sin que nadie
    # lo note (pasó con 2.1.0, publicado el 16/9 y tomado el 18/9).
    assert respuesta.data["version"] == "2.2.0"
    assert "faseRelevamiento" in respuesta.data["catalogos"]
    assert respuesta.data["cuestionario"]["paginas"]


@pytest.mark.django_db
def test_personas_observadas_solo_cuenta_cabeceras(provincia):
    """Regla del instrumento 2026: sumar todos multiplicaría el total."""
    from datacalle.services import resumen_de_casos

    entrevistador = _entrevistador(provincia)
    relevamiento = _relevamiento(provincia, equipo=[entrevistador])
    client = _cliente(entrevistador)
    grupo = str(uuid.uuid4())

    cabecera = dict(
        RESPUESTAS, grupoId=grupo, esCabeceraGrupo="si", personasObservadas=3
    )
    acompanante = dict(
        RESPUESTAS, grupoId=grupo, esCabeceraGrupo="no", personasObservadas=3
    )
    for respuestas in (cabecera, acompanante):
        client.put(
            f"/api/datacalle/encuestas/{uuid.uuid4()}/",
            _cuerpo(relevamiento, respuestas=respuestas),
            format="json",
        )

    resumen = resumen_de_casos(relevamiento)

    assert resumen["casos"] == 2
    assert resumen["personas_observadas"] == 3
    assert resumen["entrevistas"] == 2


@pytest.mark.django_db
def test_el_menor_se_distingue_de_la_negativa(provincia):
    from datacalle.services import resumen_de_casos

    entrevistador = _entrevistador(provincia)
    relevamiento = _relevamiento(provincia, equipo=[entrevistador])
    client = _cliente(entrevistador)

    menor = {k: v for k, v in RESPUESTAS.items() if k != "realizaEntrevista"}
    menor["esMenorDeEdad"] = "si"
    negativa = dict(RESPUESTAS, realizaEntrevista="noRotundo")

    client.put(
        f"/api/datacalle/encuestas/{uuid.uuid4()}/",
        _cuerpo(relevamiento, estado="rechazada", respuestas=menor),
        format="json",
    )
    client.put(
        f"/api/datacalle/encuestas/{uuid.uuid4()}/",
        _cuerpo(relevamiento, estado="rechazada", respuestas=negativa),
        format="json",
    )

    resumen = resumen_de_casos(relevamiento)

    assert resumen["menores"] == 1
    assert resumen["sin_entrevista"] == 1


@pytest.mark.django_db
def test_qa_0012_operativo_no_iniciado_rechaza_casos(provincia):
    """QA-0012: cargar antes de la fecha de inicio es un error del lado app."""
    entrevistador = _entrevistador(provincia)
    futuro = datetime.date.today() + datetime.timedelta(days=5)
    relevamiento = _relevamiento(
        provincia,
        equipo=[entrevistador],
        fecha_inicio=futuro,
        fecha_fin=futuro + datetime.timedelta(days=2),
    )

    respuesta = _cliente(entrevistador).put(
        f"/api/datacalle/encuestas/{uuid.uuid4()}/",
        _cuerpo(relevamiento),
        format="json",
    )

    assert respuesta.status_code == 409
    assert respuesta.data["codigo"] == "relevamiento_no_iniciado"
    assert Encuesta.objects.count() == 0


@pytest.mark.django_db
def test_qa_0012_el_dia_de_inicio_ya_acepta_casos(provincia):
    entrevistador = _entrevistador(provincia)
    hoy = datetime.date.today()
    relevamiento = _relevamiento(
        provincia,
        equipo=[entrevistador],
        fecha_inicio=hoy,
        fecha_fin=hoy + datetime.timedelta(days=2),
    )

    respuesta = _cliente(entrevistador).put(
        f"/api/datacalle/encuestas/{uuid.uuid4()}/",
        _cuerpo(relevamiento),
        format="json",
    )

    assert respuesta.status_code == 201


@pytest.mark.django_db
def test_la_fecha_de_fin_no_corta_la_carga(provincia):
    """El operativo puede estirarse: lo que manda es el estado, no la fecha."""
    entrevistador = _entrevistador(provincia)
    pasado = datetime.date.today() - datetime.timedelta(days=30)
    relevamiento = _relevamiento(
        provincia,
        equipo=[entrevistador],
        fecha_inicio=pasado,
        fecha_fin=pasado + datetime.timedelta(days=2),
    )

    respuesta = _cliente(entrevistador).put(
        f"/api/datacalle/encuestas/{uuid.uuid4()}/",
        _cuerpo(relevamiento),
        format="json",
    )

    assert respuesta.status_code == 201


@pytest.mark.django_db
def test_un_operativo_en_curso_acepta_casos_aunque_le_adelanten_la_fecha(provincia):
    """El estado le gana a la fecha, igual que con la fecha de fin.

    Si el coordinador corrige ``fecha_inicio`` hacia adelante después de que el
    operativo arrancó, los casos que ya se están cargando no pueden empezar a
    rebotar.
    """
    entrevistador = _entrevistador(provincia)
    futuro = datetime.date.today() + datetime.timedelta(days=5)
    relevamiento = _relevamiento(
        provincia,
        equipo=[entrevistador],
        fecha_inicio=futuro,
        fecha_fin=futuro + datetime.timedelta(days=2),
        estado=Relevamiento.Estado.EN_CURSO,
    )

    respuesta = _cliente(entrevistador).put(
        f"/api/datacalle/encuestas/{uuid.uuid4()}/",
        _cuerpo(relevamiento),
        format="json",
    )

    assert respuesta.status_code == 201


@pytest.mark.django_db
def test_los_dos_409_se_distinguen_por_reintentable(provincia):
    """No iniciado se resuelve solo; cerrado no. La app no puede confundirlos."""
    entrevistador = _entrevistador(provincia)
    futuro = datetime.date.today() + datetime.timedelta(days=5)
    no_iniciado = _relevamiento(
        provincia,
        equipo=[entrevistador],
        fecha_inicio=futuro,
        fecha_fin=futuro + datetime.timedelta(days=2),
    )
    pasado = datetime.date.today() - datetime.timedelta(days=30)
    cerrado = _relevamiento(
        provincia,
        equipo=[entrevistador],
        fecha_inicio=pasado,
        fecha_fin=pasado + datetime.timedelta(days=2),
        estado=Relevamiento.Estado.FINALIZADO,
    )
    cliente = _cliente(entrevistador)

    temprano = cliente.put(
        f"/api/datacalle/encuestas/{uuid.uuid4()}/",
        _cuerpo(no_iniciado),
        format="json",
    )
    tarde = cliente.put(
        f"/api/datacalle/encuestas/{uuid.uuid4()}/",
        _cuerpo(cerrado),
        format="json",
    )

    assert temprano.status_code == 409
    assert temprano.data["codigo"] == "relevamiento_no_iniciado"
    assert temprano.data["reintentable"] is True

    assert tarde.status_code == 409
    assert tarde.data["codigo"] == "relevamiento_cerrado"
    assert tarde.data["reintentable"] is False


@pytest.mark.django_db
def test_qa_0020_el_entrevistador_no_puede_cerrar_el_operativo(provincia):
    """QA-0020: el cierre es del coordinador, no del relevador en campo.

    El relevador comparte el operativo con el resto del equipo: si cierra,
    deja afuera a los demás.
    """
    entrevistador = _entrevistador(provincia)
    relevamiento = _relevamiento(provincia, equipo=[entrevistador])

    respuesta = _cliente(entrevistador).post(
        f"/api/datacalle/relevamientos/{relevamiento.id}/cerrar/",
        {},
        format="json",
    )

    assert respuesta.status_code == 403
    assert respuesta.data["codigo"] == "cierre_no_autorizado"
    relevamiento.refresh_from_db()
    assert relevamiento.estado == Relevamiento.Estado.PLANIFICADO
    assert relevamiento.fecha_cierre is None


@pytest.mark.django_db
def test_qa_0012_la_tarea_futura_viaja_marcada_como_no_iniciable(provincia):
    """QA-0012: el operativo futuro se baja igual, pero avisa que no arrancó.

    No se oculta: la app es offline-first y necesita tenerlo antes de salir.
    """
    entrevistador = _entrevistador(provincia)
    futuro = datetime.date.today() + datetime.timedelta(days=5)
    _relevamiento(
        provincia,
        equipo=[entrevistador],
        denominacion="Arranca la semana que viene",
        fecha_inicio=futuro,
        fecha_fin=futuro + datetime.timedelta(days=2),
    )

    respuesta = _cliente(entrevistador).get("/api/datacalle/relevamientos/")

    assert respuesta.status_code == 200
    tarea = respuesta.data["results"][0]
    assert tarea["denominacion"] == "Arranca la semana que viene"
    assert tarea["puede_iniciar"] is False


@pytest.mark.django_db
def test_qa_0012_la_tarea_de_hoy_viaja_iniciable(provincia):
    entrevistador = _entrevistador(provincia)
    hoy = datetime.date.today()
    _relevamiento(
        provincia,
        equipo=[entrevistador],
        fecha_inicio=hoy,
        fecha_fin=hoy + datetime.timedelta(days=2),
    )

    respuesta = _cliente(entrevistador).get("/api/datacalle/relevamientos/")

    assert respuesta.data["results"][0]["puede_iniciar"] is True


@pytest.mark.django_db
def test_qa_0012_la_senal_no_se_separa_del_rechazo_real(provincia):
    """``puede_iniciar`` y el 409 salen de la misma regla: no pueden divergir."""
    entrevistador = _entrevistador(provincia)
    futuro = datetime.date.today() + datetime.timedelta(days=3)
    relevamiento = _relevamiento(
        provincia,
        equipo=[entrevistador],
        fecha_inicio=futuro,
        fecha_fin=futuro + datetime.timedelta(days=1),
    )
    client = _cliente(entrevistador)

    listado = client.get("/api/datacalle/relevamientos/")
    carga = client.put(
        f"/api/datacalle/encuestas/{uuid.uuid4()}/",
        _cuerpo(relevamiento),
        format="json",
    )

    assert listado.data["results"][0]["puede_iniciar"] is False
    assert carga.status_code == 409
    assert carga.data["codigo"] == "relevamiento_no_iniciado"
