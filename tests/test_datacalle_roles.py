"""Tests de los tres roles de DataCalle (decisión 2026-09-18)."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from core.models import Provincia
from users.models import Profile, RelevadorCalleProvincia
from users.services_datacalle import (
    es_administrador_datacalle,
    es_coordinador_datacalle,
    es_solo_app,
    get_datacalle_provincia_ids,
    get_datacalle_rol,
    get_relevador_calle_provincias,
    get_relevador_calle_users_for_provincia,
    tiene_acceso_datacalle,
)


@pytest.fixture
def provincia(db):
    return Provincia.objects.create(nombre="Córdoba")


def test_existen_los_tres_roles_del_documento_funcional():
    codigos = [codigo for codigo, _ in Profile.DataCalleRol.choices]
    assert codigos == ["administrador", "coordinador", "entrevistador"]


def test_las_etiquetas_son_las_del_documento_funcional():
    etiquetas = dict(Profile.DataCalleRol.choices)
    assert etiquetas["administrador"] == "Administrador Nacional"
    assert etiquetas["coordinador"] == "Coordinador Provincial"
    assert etiquetas["entrevistador"] == "Relevador"


def _usuario(username, rol, provincia=None, staff=False):
    user = get_user_model().objects.create_user(
        username=username, email=f"{username}@example.com", password="Sisoc12345!"
    )
    user.is_staff = staff
    user.save()
    perfil = user.profile
    perfil.datacalle_rol = rol
    perfil.es_relevador_calle = bool(rol)
    if rol == "coordinador" and provincia is not None:
        perfil.es_usuario_provincial = True
    perfil.save()
    if provincia is not None:
        if rol == "entrevistador":
            RelevadorCalleProvincia.objects.create(profile=perfil, provincia=provincia)
        else:
            perfil.territorial_scopes.create(provincia=provincia)
    return user


@pytest.mark.django_db
def test_la_jerarquia_es_decreciente(provincia):
    admin = _usuario("admin_dc", "administrador", staff=True)
    coord = _usuario("coord_dc", "coordinador", provincia, staff=True)
    relevador = _usuario("relev_dc", "entrevistador", provincia)

    # Los tres acceden a la app.
    assert [tiene_acceso_datacalle(u) for u in (admin, coord, relevador)] == [
        True,
        True,
        True,
    ]
    # Coordinador incluye al administrador: el superior puede lo del inferior.
    assert es_coordinador_datacalle(admin) is True
    assert es_coordinador_datacalle(coord) is True
    assert es_coordinador_datacalle(relevador) is False
    # Administrador es solo el administrador.
    assert es_administrador_datacalle(admin) is True
    assert es_administrador_datacalle(coord) is False
    # Solo-app es solo el relevador: es quien no entra a SISOC.
    assert [es_solo_app(u) for u in (admin, coord, relevador)] == [False, False, True]


@pytest.mark.django_db
def test_el_administrador_no_tiene_restriccion_territorial(provincia):
    admin = _usuario("admin_terr", "administrador", staff=True)
    coord = _usuario("coord_terr", "coordinador", provincia, staff=True)
    relevador = _usuario("relev_terr", "entrevistador", provincia)

    assert get_datacalle_provincia_ids(admin) is None
    assert get_datacalle_provincia_ids(coord) == [provincia.id]
    assert get_datacalle_provincia_ids(relevador) == [provincia.id]


@pytest.mark.django_db
def test_un_usuario_sin_rol_no_accede(provincia):
    ajeno = get_user_model().objects.create_user(
        username="ajeno", email="ajeno@example.com", password="Sisoc12345!"
    )

    assert get_datacalle_rol(ajeno) == ""
    assert tiene_acceso_datacalle(ajeno) is False
    assert es_coordinador_datacalle(ajeno) is False
    assert get_datacalle_provincia_ids(ajeno) == []


@pytest.mark.django_db
def test_el_equipo_del_operativo_solo_ofrece_relevadores(provincia):
    """El coordinador tambien lleva el flag ahora: no puede colarse al equipo."""
    relevador = _usuario("relev_equipo", "entrevistador", provincia)
    _usuario("coord_equipo", "coordinador", provincia, staff=True)

    disponibles = get_relevador_calle_users_for_provincia(provincia.id)

    assert [u.username for u in disponibles] == [relevador.username]


from users.forms import UserCreationForm


@pytest.mark.django_db
def test_el_coordinador_creado_conserva_el_acceso_al_backoffice(provincia):
    """El flag ya no degrada a no-staff: eso vale solo para el relevador."""
    from users.services_datacalle import es_solo_app

    coord = _usuario("coord_staff", "coordinador", provincia, staff=True)
    relevador = _usuario("relev_staff", "entrevistador", provincia)

    assert es_solo_app(coord) is False
    assert es_solo_app(relevador) is True
    # El coordinador es de backoffice; el relevador no.
    assert coord.is_staff is True
    assert relevador.is_staff is False


@pytest.mark.django_db
def test_las_provincias_del_api_salen_de_donde_corresponde_segun_el_rol(provincia):
    """QA D1.2 (/api/users/me/): el administrador no puede devolver ``[]``.

    Dos provincias para que "todas" (administrador) se distinga de "una sola"
    (coordinador y entrevistador, cada uno con su propio alcance).
    """
    otra_provincia = Provincia.objects.create(nombre="Salta")
    admin = _usuario("admin_prov_api", "administrador", staff=True)
    coord = _usuario("coord_prov_api", "coordinador", provincia, staff=True)
    relevador = _usuario("relev_prov_api", "entrevistador", provincia)

    assert get_relevador_calle_provincias(relevador) == [
        {"id": provincia.id, "nombre": provincia.nombre}
    ]
    assert get_relevador_calle_provincias(coord) == [
        {"id": provincia.id, "nombre": provincia.nombre}
    ]
    assert get_relevador_calle_provincias(admin) == [
        {"id": provincia.id, "nombre": provincia.nombre},
        {"id": otra_provincia.id, "nombre": otra_provincia.nombre},
    ]


def test_la_semilla_define_el_grupo_de_administrador():
    from users.bootstrap.groups_seed import BOOTSTRAP_GROUPS

    por_nombre = {seed.name: seed for seed in BOOTSTRAP_GROUPS}

    assert "Administrador DataCalle" in por_nombre
    admin = set(por_nombre["Administrador DataCalle"].permission_codes)
    coord = set(por_nombre["Coordinador DataCalle"].permission_codes)
    # La jerarquia es decreciente: el administrador puede todo lo del coordinador.
    assert coord <= admin


from django.db import IntegrityError, transaction


@pytest.mark.django_db
def test_un_relevador_no_puede_tener_dos_provincias(provincia):
    """RN01: provincia unica, garantizada por la base y no solo por el form."""
    salta = Provincia.objects.create(nombre="Salta")
    relevador = _usuario("relev_unica", "entrevistador", provincia)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            RelevadorCalleProvincia.objects.create(
                profile=relevador.profile, provincia=salta
            )


@pytest.mark.django_db
def test_el_form_rechaza_dos_provincias_para_un_relevador(provincia):
    """RN01 tambien en el form: ``elif len(provincias) > 1`` de
    ``_clean_relevador_calle_fields``, que la constraint de base no ejercita.

    El actor es superusuario porque es quien ve el campo completo y puede
    mandar dos provincias: un coordinador provincial tiene el campo fijo y
    deshabilitado a su unica provincia (QA-0016), asi que nunca llegaria a
    disparar esta rama.
    """
    salta = Provincia.objects.create(nombre="Salta")
    superusuario = get_user_model().objects.create_superuser(
        username="super_alta", email="super_alta@example.com", password="Sisoc12345!"
    )

    form = UserCreationForm(
        actor=superusuario,
        data={
            "username": "relev_dos_prov",
            "tipo_usuario": "interno",
            "email": "",
            "password": "Sisoc12345!",
            "es_relevador_calle": "on",
            "datacalle_rol": "entrevistador",
            "provincias_datacalle": [provincia.id, salta.id],
        },
    )

    assert form.is_valid() is False
    assert "provincias_datacalle" in form.errors


@pytest.mark.django_db
def test_solo_el_relevador_queda_afuera_del_backoffice(client, provincia):
    """RN05: el relevador no entra a SISOC; coordinador y admin si.

    Este cambio (``confirm_login_allowed`` usa ``es_solo_app``) ya estaba
    aplicado antes de esta tarea, para no dejar a los coordinadores afuera
    del backoffice durante el resto del plan. El test se agrega igual, para
    documentar la invariante y protegerla de una regresion.
    """
    _usuario("coord_login", "coordinador", provincia, staff=True)
    _usuario("relev_login", "entrevistador", provincia)

    # Dos clientes distintos: con el mismo `client` para ambos posts, la
    # sesion ya autenticada del coordinador sobrevive al intento rechazado
    # del relevador (la validacion falla antes de tocar la sesion) y el
    # segundo response queda con el usuario equivocado.
    entra = client.post(
        "/login/",
        {"username": "coord_login", "password": "Sisoc12345!"},
        follow=True,
    )
    rebota = Client().post(
        "/login/",
        {"username": "relev_login", "password": "Sisoc12345!"},
        follow=True,
    )

    assert entra.context["user"].is_authenticated is True
    assert rebota.context["user"].is_authenticated is False
    assert "SISOC - Mobile DataCalle" in rebota.content.decode()


@pytest.mark.django_db
def test_los_tres_roles_obtienen_token_de_la_app(provincia):
    """Matriz punto 5: los tres acceden a DataCalle."""
    from rest_framework.test import APIClient

    _usuario("admin_token", "administrador", staff=True)
    _usuario("coord_token", "coordinador", provincia, staff=True)
    _usuario("relev_token", "entrevistador", provincia)

    for username in ("admin_token", "coord_token", "relev_token"):
        respuesta = APIClient().post(
            "/api/users/login/",
            {"username": username, "password": "Sisoc12345!"},
            format="json",
        )
        assert respuesta.status_code == 200, username
        assert respuesta.data["token"]


@pytest.mark.django_db
def test_el_flag_sin_rol_no_alcanza_para_entrar_a_la_app(provincia):
    """RN05: el gate de la API mira el rol, no el flag.

    ``es_relevador_calle`` hoy siempre viaja junto al rol (ver ``_usuario``),
    asi que probar solo los tres roles no distingue si el gate quedo mirando
    el flag o el rol: con ``is_relevador_calle_user`` tambien hubiera pasado.
    Este test arma a mano un usuario con el flag prendido pero sin rol -algo
    que hoy no ocurre por los caminos normales de alta, pero que el gate debe
    igual rechazar- para que la asercion dependa realmente del criterio nuevo.
    """
    from rest_framework.test import APIClient

    ajeno = _usuario("flag_sin_rol", "", provincia)
    perfil = ajeno.profile
    perfil.datacalle_rol = ""
    perfil.es_relevador_calle = True
    perfil.save()

    assert tiene_acceso_datacalle(ajeno) is False

    respuesta = APIClient().post(
        "/api/users/login/",
        {"username": "flag_sin_rol", "password": "Sisoc12345!"},
        format="json",
    )

    assert respuesta.status_code == 401
    assert respuesta.data["detail"] == "Este usuario no tiene acceso PWA activo."


@pytest.mark.django_db
def test_las_modificaciones_del_operativo_quedan_registradas(provincia):
    """8.6: quien modifico que y cuando, mas alla de creado_por/cerrado_por."""
    import datetime

    from auditlog.models import LogEntry

    from datacalle.models import Relevamiento

    relevamiento = Relevamiento.objects.create(
        denominacion="Operativo auditado",
        provincia=provincia,
        fase=Relevamiento.Fase.ESPACIO_PUBLICO,
        area_operativa="Plaza",
        fecha_inicio=datetime.date(2026, 9, 20),
        fecha_fin=datetime.date(2026, 9, 21),
    )
    relevamiento.denominacion = "Operativo auditado y renombrado"
    relevamiento.save()

    entradas = LogEntry.objects.get_for_object(relevamiento)

    assert entradas.count() >= 2  # alta + modificacion
    # No alcanza con que la clave este: si auditlog quedara mal cableado y
    # registrara el campo con valores basura, `"denominacion" in changes`
    # pasaria igual. `changes` tiene la forma {campo: [viejo, nuevo]}.
    assert entradas.first().changes["denominacion"] == [
        "Operativo auditado",
        "Operativo auditado y renombrado",
    ]


@pytest.mark.django_db
def test_el_contenido_de_las_respuestas_no_queda_en_el_log_de_auditoria(provincia):
    """8.6 + privacidad: se audita que el caso cambio, no el instrumento.

    `respuestas` guarda lo relevado a una persona en situacion de calle. El
    log de auditoria es exportable (audittrail) y sobrevive al borrado del
    caso, asi que copiar ese JSON ahi seria una fuga de datos sensibles.

    Lo mismo vale para las columnas indexadas que `_copiar_columnas_indexadas`
    saca de ese instrumento (`lat`/`lon`, `codigo_entrevistado`,
    `persona_entrevistada`, `es_menor_de_edad`): excluir solo `respuestas` y
    dejar pasar estas columnas deja el mismo agujero abierto por otra puerta.
    """
    import datetime

    from auditlog.models import LogEntry

    from datacalle.models import Encuesta, Relevamiento

    relevamiento = Relevamiento.objects.create(
        denominacion="Operativo con casos auditados",
        provincia=provincia,
        fase=Relevamiento.Fase.ESPACIO_PUBLICO,
        area_operativa="Plaza",
        fecha_inicio=datetime.date(2026, 9, 20),
        fecha_fin=datetime.date(2026, 9, 21),
    )
    dato_sensible = "Juan Secreto Perez"
    lat_sensible = -34.603722
    lon_sensible = -58.381592
    codigo_sensible = "COD-DISTINTIVO-2026"
    persona_sensible = "mujer_adulta_mayor_distintiva"
    encuesta = Encuesta.objects.create(
        relevamiento=relevamiento,
        estado=Encuesta.Estado.COMPLETA,
        respuestas={"nombre": dato_sensible},
        lat=lat_sensible,
        lon=lon_sensible,
        codigo_entrevistado=codigo_sensible,
        persona_entrevistada=persona_sensible,
        es_menor_de_edad=True,
    )
    encuesta.estado = Encuesta.Estado.RECHAZADA
    encuesta.respuestas = {"nombre": dato_sensible, "edad": 40}
    encuesta.lat = lat_sensible + 1
    encuesta.lon = lon_sensible + 1
    encuesta.codigo_entrevistado = codigo_sensible + "-MOD"
    encuesta.persona_entrevistada = persona_sensible + "-mod"
    encuesta.es_menor_de_edad = False
    encuesta.save()

    entradas = LogEntry.objects.get_for_object(encuesta)

    assert entradas.count() >= 2  # alta + modificacion

    campos_excluidos = (
        "respuestas",
        "lat",
        "lon",
        "codigo_entrevistado",
        "persona_entrevistada",
        "es_menor_de_edad",
    )
    valores_sensibles = (
        dato_sensible,
        codigo_sensible,
        persona_sensible,
        str(lat_sensible),
        str(lon_sensible),
    )
    for entrada in entradas:
        for campo in campos_excluidos:
            assert campo not in entrada.changes
        # Aserto sobre el contenido, no solo sobre la clave: si mañana
        # alguien saca un campo de `excluded_fields` en audittrail/constants
        # pero deja el nombre del campo intacto, este assert lo detecta
        # igual porque compara contra los valores, no contra las claves.
        for valor in valores_sensibles:
            assert valor not in str(entrada.changes)


@pytest.mark.django_db
def test_el_cierre_del_operativo_no_deja_ubicacion_ni_observaciones_en_el_log(
    provincia,
):
    """Mismo agujero que el test anterior, pero en Relevamiento.

    `cerrar_relevamiento` completa `lat`/`lon` (coordenadas GPS exactas del
    cierre) y `observacion_asentamiento`/`otra_observacion` (como vive el
    grupo en ese punto, la segunda en texto libre) en cada cierre de
    operativo. Es mas sensible que un caso individual porque describe a todo
    un grupo, asi que audittrail/constants.py debe excluirlos igual.
    """
    import datetime

    from datacalle.models import Relevamiento
    from datacalle.services.encuestas import cerrar_relevamiento
    from auditlog.models import LogEntry

    relevamiento = Relevamiento.objects.create(
        denominacion="Operativo a cerrar",
        provincia=provincia,
        fase=Relevamiento.Fase.ESPACIO_PUBLICO,
        area_operativa="Plaza",
        fecha_inicio=datetime.date(2026, 9, 20),
        fecha_fin=datetime.date(2026, 9, 21),
    )
    lat_sensible = -34.612345
    lon_sensible = -58.412345
    observacion_sensible = "asentamiento_precario_distintivo"
    texto_sensible = "Grupo familiar junto al puente, colchones y una carpa azul"
    usuario = get_user_model().objects.create_user(
        username="cierre_operativo",
        email="cierre_operativo@example.com",
        password="Sisoc12345!",
    )

    cerrar_relevamiento(
        relevamiento=relevamiento,
        user=usuario,
        datos={
            "lat": lat_sensible,
            "lon": lon_sensible,
            "observacion_asentamiento": [observacion_sensible],
            "otra_observacion": texto_sensible,
        },
    )

    entradas = LogEntry.objects.get_for_object(relevamiento)
    assert entradas.count() >= 1

    campos_excluidos = (
        "lat",
        "lon",
        "observacion_asentamiento",
        "otra_observacion",
    )
    valores_sensibles = (
        str(lat_sensible),
        str(lon_sensible),
        observacion_sensible,
        texto_sensible,
    )
    for entrada in entradas:
        for campo in campos_excluidos:
            assert campo not in entrada.changes
        # Igual que en el test de Encuesta: aserto sobre los valores, no
        # sobre las claves, para que la prueba falle si alguien saca un
        # campo de `excluded_fields` pero deja el nombre intacto.
        for valor in valores_sensibles:
            assert valor not in str(entrada.changes)


@pytest.mark.django_db
def test_object_repr_de_una_encuesta_no_lleva_el_codigo_del_entrevistado(provincia):
    """`object_repr` bypasea `excluded_fields`: sale de `__str__`, no de `changes`.

    django-auditlog arma `LogEntry.object_repr` con `smart_str(instance)`
    (o sea `Encuesta.__str__`) sin pasar por ningun filtro de campos, y ese
    log es exportable y visible en `/admin/auditlog/logentry/` con el
    permiso estandar de Django. Si `__str__` devolviera el codigo del
    entrevistado -como hacia antes-, quedaria grabado igual pese a estar
    excluido de `changes`.
    """
    import datetime

    from datacalle.models import Encuesta, Relevamiento
    from auditlog.models import LogEntry

    relevamiento = Relevamiento.objects.create(
        denominacion="Operativo con caso identificable",
        provincia=provincia,
        fase=Relevamiento.Fase.ESPACIO_PUBLICO,
        area_operativa="Plaza",
        fecha_inicio=datetime.date(2026, 9, 20),
        fecha_fin=datetime.date(2026, 9, 21),
    )
    codigo_sensible = "COD-OBJECT-REPR-2026"

    encuesta = Encuesta.objects.create(
        relevamiento=relevamiento,
        estado=Encuesta.Estado.COMPLETA,
        codigo_entrevistado=codigo_sensible,
    )

    entradas = LogEntry.objects.get_for_object(encuesta)
    assert entradas.count() >= 1
    for entrada in entradas:
        assert codigo_sensible not in entrada.object_repr


# ---------------------------------------------------------------------------
# Revisión final de la rama (2026-09-19): el rol de DataCalle y el alcance
# territorial del backoffice eran dos mundos desconectados.
# ---------------------------------------------------------------------------


def _superusuario(username="super_fix"):
    return get_user_model().objects.create_superuser(
        username=username, email=f"{username}@example.com", password="Sisoc12345!"
    )


def _datos_edicion(user, **extra):
    datos = {
        "username": user.username,
        "tipo_usuario": "interno",
        "email": "",
        "password": "",
    }
    datos.update(extra)
    return datos


def _crear_por_formulario(actor, username, rol, provincia=None, **extra):
    """Alta por el formulario real: es el camino que dejaba el alcance roto."""
    from users.forms import UserCreationForm

    datos = {
        "username": username,
        "email": f"{username}@example.com",
        "password": "Sisoc12345!",
        "tipo_usuario": "interno",
        "es_relevador_calle": "on",
        "datacalle_rol": rol,
    }
    if provincia is not None:
        datos["provincias_datacalle"] = [provincia.id]
    datos.update(extra)
    form = UserCreationForm(actor=actor, data=datos)
    assert form.is_valid(), form.errors
    return form.save()


@pytest.mark.django_db
def test_el_coordinador_puede_guardar_su_propio_registro(provincia):
    """BLOQUEANTE: el rol propio tiene que estar en las choices del select.

    ``initial`` decía "coordinador" pero las choices del actor no lo incluían,
    así que el ``<select>`` no contenía el valor actual, el browser posteaba
    ``""`` y el formulario se rechazaba con "Seleccione una opción válida". Un
    coordinador no podía ni corregirse el mail, y lo único que la pantalla le
    ofrecía era "Relevador", que lo degradaba a no-staff y lo expulsaba de
    SISOC en el próximo login.
    """
    from users.forms import CustomUserChangeForm

    coord = _usuario("coord_autoedita", "coordinador", provincia, staff=True)

    form = CustomUserChangeForm(instance=coord, actor=coord)
    ofrecidos = [codigo for codigo, _ in form.fields["datacalle_rol"].choices if codigo]
    assert "coordinador" in ofrecidos

    form = CustomUserChangeForm(
        instance=coord,
        actor=coord,
        data=_datos_edicion(
            coord,
            first_name="Nombre Corregido",
            es_relevador_calle="on",
            datacalle_rol="coordinador",
            provincias_datacalle=[provincia.id],
        ),
    )

    assert form.is_valid(), form.errors
    form.save()
    coord.refresh_from_db()
    coord.profile.refresh_from_db()
    assert coord.first_name == "Nombre Corregido"
    # No se autodegradó: sigue siendo coordinador y sigue entrando a SISOC.
    assert coord.profile.datacalle_rol == "coordinador"
    assert coord.is_staff is True


@pytest.mark.django_db
def test_sin_actor_el_selector_de_rol_es_fail_closed(provincia):
    """Sin actor sólo se puede asignar "Relevador".

    Antes devolvía los tres roles (fail-open), así que cualquier camino que
    instanciara el formulario sin actor podía asignar el rol más alto.
    """
    from users.forms import UserCreationForm

    form = UserCreationForm()
    ofrecidos = [codigo for codigo, _ in form.fields["datacalle_rol"].choices if codigo]

    assert ofrecidos == ["entrevistador"]


@pytest.mark.django_db
def test_el_coordinador_del_formulario_ve_solo_su_provincia(provincia):
    """BLOQUEANTE: las dos mitades del alcance, que es el bug que casi mergeamos.

    La provincia elegida se escribía en ``RelevadorCalleProvincia``, tabla que
    sólo lee el entrevistador. El coordinador quedaba sin
    ``es_usuario_provincial`` y sin ``ProfileTerritorialScope``: en el
    backoffice eso es **sin restricción** (veía, editaba, borraba y cerraba
    operativos de todo el país, con el equipo y sus DNI) y en la app era
    alcance vacío (cero operativos).
    """
    import datetime

    from datacalle.models import Relevamiento
    from datacalle.services.relevamientos import apply_relevamientos_scope

    salta = Provincia.objects.create(nombre="Salta")
    coord = _crear_por_formulario(
        _superusuario("super_alcance"), "coord_alcance", "coordinador", provincia
    )
    perfil = coord.profile

    # El sistema armó el alcance solo (D1), en la tabla que leen los lectores.
    assert perfil.es_usuario_provincial is True
    assert list(perfil.territorial_scopes.values_list("provincia_id", flat=True)) == [
        provincia.id
    ]
    # Y no ensució la tabla del entrevistador.
    assert perfil.relevador_calle_provincias.exists() is False

    propio = Relevamiento.objects.create(
        denominacion="Operativo propio",
        provincia=provincia,
        fase=Relevamiento.Fase.ESPACIO_PUBLICO,
        area_operativa="Plaza",
        fecha_inicio=datetime.date(2026, 9, 20),
        fecha_fin=datetime.date(2026, 9, 21),
    )
    Relevamiento.objects.create(
        denominacion="Operativo ajeno",
        provincia=salta,
        fase=Relevamiento.Fase.ESPACIO_PUBLICO,
        area_operativa="Plaza",
        fecha_inicio=datetime.date(2026, 9, 20),
        fecha_fin=datetime.date(2026, 9, 21),
    )

    # Mitad backoffice: sólo su provincia.
    visibles = apply_relevamientos_scope(Relevamiento.objects.all(), coord)
    assert [r.pk for r in visibles] == [propio.pk]
    # Mitad app: su provincia, no la lista vacía.
    assert get_datacalle_provincia_ids(coord) == [provincia.id]
    assert get_relevador_calle_provincias(coord) == [
        {"id": provincia.id, "nombre": provincia.nombre}
    ]


@pytest.mark.django_db
def test_el_administrador_del_formulario_queda_sin_alcance(provincia):
    """Alcance nacional es, literalmente, no tener alcance."""
    admin = _crear_por_formulario(
        _superusuario("super_admin_form"), "admin_form", "administrador"
    )
    perfil = admin.profile

    assert perfil.es_usuario_provincial is False
    assert perfil.territorial_scopes.exists() is False
    assert perfil.relevador_calle_provincias.exists() is False
    assert get_datacalle_provincia_ids(admin) is None


@pytest.mark.django_db
def test_pasar_de_relevador_a_coordinador_limpia_la_tabla_del_relevador(provincia):
    """``_sync_relevador_calle_provincias`` escribía filas para los tres roles."""
    from users.forms import CustomUserChangeForm

    relevador = _usuario("muta_rol", "entrevistador", provincia)
    assert relevador.profile.relevador_calle_provincias.exists() is True

    form = CustomUserChangeForm(
        instance=relevador,
        actor=_superusuario("super_muta"),
        data=_datos_edicion(
            relevador,
            es_relevador_calle="on",
            datacalle_rol="coordinador",
            provincias_datacalle=[provincia.id],
        ),
    )

    assert form.is_valid(), form.errors
    form.save()
    perfil = relevador.profile
    perfil.refresh_from_db()
    assert perfil.relevador_calle_provincias.exists() is False
    assert list(perfil.territorial_scopes.values_list("provincia_id", flat=True)) == [
        provincia.id
    ]


@pytest.mark.django_db
def test_el_coordinador_del_formulario_recibe_su_grupo(provincia):
    """D1: el operador elige el rol y el sistema asigna el grupo."""
    from django.contrib.auth.models import Group

    Group.objects.get_or_create(name="Coordinador DataCalle")
    coord = _crear_por_formulario(
        _superusuario("super_grupo"), "coord_grupo", "coordinador", provincia
    )

    assert coord.groups.filter(name="Coordinador DataCalle").exists()


@pytest.mark.django_db
def test_un_usuario_provincial_no_puede_cambiarse_la_provincia(provincia):
    """RN02, también por POST: lo único ``disabled`` era el campo equivocado.

    ``provincias_datacalle`` es la tabla del entrevistador; la provincia del
    coordinador vive en ``ProfileTerritorialScope``, y por ahí se mudaba solo.
    """
    import json

    from users.forms import CustomUserChangeForm

    salta = Provincia.objects.create(nombre="Salta")
    coord = _usuario("coord_se_muda", "coordinador", provincia, staff=True)

    form = CustomUserChangeForm(
        instance=coord,
        actor=coord,
        data=_datos_edicion(
            coord,
            es_relevador_calle="on",
            datacalle_rol="coordinador",
            provincias_datacalle=[salta.id],
            es_usuario_provincial="on",
            territorial_scopes=json.dumps(
                [
                    {
                        "provincia_id": salta.id,
                        "municipio_id": None,
                        "localidad_id": None,
                    }
                ]
            ),
        ),
    )

    assert form.is_valid(), form.errors
    form.save()
    coord.profile.refresh_from_db()
    assert list(
        coord.profile.territorial_scopes.values_list("provincia__nombre", flat=True)
    ) == [provincia.nombre]


@pytest.mark.django_db
def test_el_rol_del_perfil_llega_a_la_api_sin_el_flag(provincia):
    """``/api/users/me/`` leía el rol detrás de ``es_relevador_calle``.

    Un perfil con rol y sin flag entra a la API por ``TieneAccesoDataCalle``
    -que mira el rol- y después ``/me/`` le contestaba que no tenía ninguno.
    """
    from users.api_serializers import UserContextSerializer

    coord = _usuario("coord_api_rol", "coordinador", provincia, staff=True)
    perfil = coord.profile
    perfil.es_relevador_calle = False
    perfil.save(update_fields=["es_relevador_calle"])

    datos = UserContextSerializer(coord).data

    assert datos["profile"]["es_relevador_calle"] is False
    assert datos["profile"]["datacalle_rol"] == "coordinador"


@pytest.mark.django_db
def test_la_migracion_0053_clasifica_por_la_restriccion_territorial(provincia):
    """E: la migración clasificaba con el predicado equivocado, dos veces.

    Primero usaba ``territorial_scopes.exists()``: un perfil con scopes pero
    sin ``es_usuario_provincial`` quedaba ``coordinador`` cuando en runtime los
    lectores lo tratan como nacional. Después pasó a
    ``get_full_province_scope_ids``, que arregla ese caso pero mete en la misma
    bolsa al provincial con alcance **sólo municipal**: el predicado de alcance
    efectivo no distingue "sin restricción" de "restricción municipal", y para
    decidir un rol esa diferencia es todo. Ahora la pregunta es la restricción:
    quien la tiene activa queda ``coordinador``, tenga provincia completa o un
    único municipio.
    """
    import importlib

    from django.apps import apps as global_apps
    from django.contrib.auth.models import Group

    from core.models import Municipio

    migracion = importlib.import_module("users.migrations.0053_datacalle_tres_roles")
    grupo, _ = Group.objects.get_or_create(name="Coordinador DataCalle")

    def _con_grupo(username):
        user = get_user_model().objects.create_user(
            username=username, email=f"{username}@example.com", password="Sisoc12345!"
        )
        user.groups.add(grupo)
        return user

    # Scopes pero sin el flag: los servicios lo leen como nacional.
    sin_flag = _con_grupo("mig_sin_flag")
    sin_flag.profile.territorial_scopes.create(provincia=provincia)
    # Provincial con provincia completa: coordinador de verdad.
    completo = _con_grupo("mig_completo")
    completo.profile.es_usuario_provincial = True
    completo.profile.save()
    completo.profile.territorial_scopes.create(provincia=provincia)
    # Provincial pero sólo con alcance municipal: hoy en el backoffice
    # ``apply_relevamientos_scope`` le devuelve ``.none()``, o sea que no ve
    # nada. Ascenderlo a ``administrador`` -que es lo que hacía clasificar por
    # ``get_full_province_scope_ids``- le regalaba el país entero.
    municipal = _con_grupo("mig_municipal")
    municipal.profile.es_usuario_provincial = True
    municipal.profile.save()
    municipio = Municipio.objects.create(nombre="Capital", provincia=provincia)
    municipal.profile.territorial_scopes.create(
        provincia=provincia, municipio=municipio
    )

    migracion.asignar_rol_a_coordinadores_existentes(global_apps, None)

    for user, esperado in (
        (sin_flag, "administrador"),
        (completo, "coordinador"),
        # Mínimo privilegio: con la restricción activa va a ``coordinador``.
        (municipal, "coordinador"),
    ):
        user.profile.refresh_from_db()
        assert user.profile.datacalle_rol == esperado, user.username


@pytest.mark.django_db
def test_la_migracion_0053_tambien_migra_a_los_relevadores(provincia):
    """F: un perfil con el flag y sin rol perdía la app y ganaba el backoffice."""
    import importlib

    from django.apps import apps as global_apps
    from django.contrib.auth.models import Group

    migracion = importlib.import_module("users.migrations.0053_datacalle_tres_roles")
    grupo, _ = Group.objects.get_or_create(name="Coordinador DataCalle")

    relevador = get_user_model().objects.create_user(
        username="mig_relevador", email="mr@example.com", password="Sisoc12345!"
    )
    relevador.profile.es_relevador_calle = True
    relevador.profile.save()

    coordinador = get_user_model().objects.create_user(
        username="mig_coord_flag", email="mc@example.com", password="Sisoc12345!"
    )
    coordinador.groups.add(grupo)
    coordinador.profile.es_relevador_calle = True
    coordinador.profile.es_usuario_provincial = True
    coordinador.profile.save()
    coordinador.profile.territorial_scopes.create(provincia=provincia)

    migracion.asignar_rol_a_coordinadores_existentes(global_apps, None)
    migracion.asignar_rol_a_relevadores_existentes(global_apps, None)
    # Idempotente: volver a correrla no pisa nada.
    migracion.asignar_rol_a_relevadores_existentes(global_apps, None)

    relevador.profile.refresh_from_db()
    coordinador.profile.refresh_from_db()
    assert relevador.profile.datacalle_rol == "entrevistador"
    assert coordinador.profile.datacalle_rol == "coordinador"


# ---------------------------------------------------------------------------
# Segunda revisión (2026-09-19): el rol de DataCalle no puede reescribir el
# panel territorial genérico del backoffice.
# ---------------------------------------------------------------------------


def _con_alcance(username, provincias, municipio=None):
    """Usuario del backoffice con alcance territorial ya cargado."""
    user = get_user_model().objects.create_user(
        username=username, email=f"{username}@example.com", password="Sisoc12345!"
    )
    user.is_staff = True
    user.save()
    perfil = user.profile
    perfil.es_usuario_provincial = True
    perfil.save()
    for prov in provincias:
        perfil.territorial_scopes.create(provincia=prov, municipio=municipio)
    return user


@pytest.mark.django_db
def test_el_rol_coordinador_no_le_borra_las_otras_provincias(provincia):
    """BLOQUEANTE: ``es_usuario_provincial`` y ``ProfileTerritorialScope`` no son
    de DataCalle, son el panel territorial que comparten comedores, admisiones
    y SIMEPI.

    ``_derivar_alcance_datacalle`` los reescribía según el rol, así que un
    usuario con tres provincias al que se le asignaba ``coordinador`` de
    Córdoba perdía Salta y Jujuy en todos esos módulos, sin error y sin aviso.
    La decisión es rechazar, no pisar.
    """
    from users.forms import CustomUserChangeForm

    salta = Provincia.objects.create(nombre="Salta")
    jujuy = Provincia.objects.create(nombre="Jujuy")
    usuario = _con_alcance("tres_provincias", [provincia, salta, jujuy])

    form = CustomUserChangeForm(
        instance=usuario,
        actor=_superusuario("super_conflicto"),
        data=_datos_edicion(
            usuario,
            es_relevador_calle="on",
            datacalle_rol="coordinador",
            provincias_datacalle=[provincia.id],
        ),
    )

    assert form.is_valid() is False
    mensaje = " ".join(form.errors["datacalle_rol"])
    # Accionable: cuántas tiene hoy, cuáles, qué perdería y qué hacer antes.
    assert "3 provincias" in mensaje
    assert "Salta" in mensaje
    assert "comedores" in mensaje
    assert "alcance territorial" in mensaje
    # Y no se guardó nada a medias.
    usuario.profile.refresh_from_db()
    assert usuario.profile.territorial_scopes.count() == 3
    assert usuario.profile.datacalle_rol == ""


@pytest.mark.django_db
def test_el_rol_administrador_no_deja_irrestricto_al_que_tenia_alcance(provincia):
    """El administrador nacional no tiene alcance: quitárselo a un usuario que
    sí lo tenía lo vuelve irrestricto en **todo** el backoffice, no sólo en
    DataCalle."""
    from users.forms import CustomUserChangeForm

    usuario = _con_alcance("una_provincia", [provincia])

    form = CustomUserChangeForm(
        instance=usuario,
        actor=_superusuario("super_conflicto_admin"),
        data=_datos_edicion(
            usuario,
            es_relevador_calle="on",
            datacalle_rol="administrador",
        ),
    )

    assert form.is_valid() is False
    mensaje = " ".join(form.errors["datacalle_rol"])
    assert "1 provincia" in mensaje
    assert "sin restricción territorial en todo el backoffice" in mensaje
    usuario.profile.refresh_from_db()
    assert usuario.profile.es_usuario_provincial is True
    assert usuario.profile.territorial_scopes.count() == 1


@pytest.mark.django_db
def test_un_alcance_municipal_no_se_ensancha_al_hacerlo_coordinador(provincia):
    """Derivar a provincia completa a quien hoy sólo ve un municipio le
    **ensancha** el acceso en los otros módulos: también es conflicto."""
    from core.models import Municipio
    from users.forms import CustomUserChangeForm

    municipio = Municipio.objects.create(nombre="Capital", provincia=provincia)
    usuario = _con_alcance("solo_municipio", [provincia], municipio=municipio)

    form = CustomUserChangeForm(
        instance=usuario,
        actor=_superusuario("super_conflicto_muni"),
        data=_datos_edicion(
            usuario,
            es_relevador_calle="on",
            datacalle_rol="coordinador",
            provincias_datacalle=[provincia.id],
        ),
    )

    assert form.is_valid() is False
    mensaje = " ".join(form.errors["datacalle_rol"])
    assert "municipal" in mensaje
    # Un solo error: no se repite "le falta una provincia completa".
    assert "provincias_datacalle" not in form.errors


@pytest.mark.django_db
def test_el_alta_sin_alcance_previo_si_deriva_la_provincia(provincia):
    """El caso común del alta sigue andando: sin alcance cargado no hay
    conflicto y el sistema arma el alcance solo (D1)."""
    coord = _crear_por_formulario(
        _superusuario("super_sin_alcance"),
        "coord_sin_alcance",
        "coordinador",
        provincia,
    )

    perfil = coord.profile
    assert perfil.es_usuario_provincial is True
    assert list(perfil.territorial_scopes.values_list("provincia_id", flat=True)) == [
        provincia.id
    ]
