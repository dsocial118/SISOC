"""Tests del ABM de relevamientos DataCalle (D2: planificación desde SISOC)."""

import datetime

import pytest
from django.contrib.auth import get_user_model

from core.models import Localidad, Municipio, Provincia
from datacalle.forms import RelevamientoForm
from datacalle.models import Relevamiento
from datacalle.services import (
    apply_relevamientos_scope,
    delete_relevamiento,
    get_entrevistadores_para_usuario,
    get_provincias_para_usuario,
    get_relevamientos_queryset,
    marcar_en_curso,
    save_relevamiento_from_form,
)
from users.models import RelevadorCalleProvincia


@pytest.fixture
def provincias(db):
    return (
        Provincia.objects.create(nombre="Córdoba"),
        Provincia.objects.create(nombre="Salta"),
    )


def _crear_entrevistador(provincia, username):
    user = get_user_model().objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="Sisoc12345!",
    )
    user.profile.es_relevador_calle = True
    user.profile.datacalle_rol = "entrevistador"
    user.profile.save()
    RelevadorCalleProvincia.objects.create(profile=user.profile, provincia=provincia)
    return user


def _crear_coordinador(provincia, username="coord"):
    user = get_user_model().objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="Sisoc12345!",
    )
    user.profile.es_usuario_provincial = True
    user.profile.save()
    user.profile.territorial_scopes.create(provincia=provincia)
    return user


def _crear_relevamiento(provincia, denominacion):
    return Relevamiento.objects.create(
        denominacion=denominacion,
        provincia=provincia,
        fase=Relevamiento.Fase.ESPACIO_PUBLICO,
        area_operativa="Plaza",
        fecha_inicio=datetime.date(2026, 9, 15),
        fecha_fin=datetime.date(2026, 9, 19),
    )


def _datos_form(provincia, equipo, **extra):
    datos = {
        "denominacion": "Operativo invierno",
        "provincia": provincia.id,
        "fase": Relevamiento.Fase.ESPACIO_PUBLICO,
        "area_operativa": "Plaza San Martín",
        "fecha_inicio": "2026-09-15",
        "fecha_fin": "2026-09-19",
        "equipo": [u.id for u in equipo],
    }
    datos.update(extra)
    return datos


@pytest.mark.django_db
def test_planifica_relevamiento_con_equipo(provincias):
    cordoba, _ = provincias
    entrevistador = _crear_entrevistador(cordoba, "entrev_cba")
    coordinador = _crear_coordinador(cordoba)

    form = RelevamientoForm(
        data=_datos_form(cordoba, [entrevistador]), actor=coordinador
    )
    assert form.is_valid(), form.errors
    relevamiento = save_relevamiento_from_form(form, user=coordinador)

    assert relevamiento.estado == Relevamiento.Estado.PLANIFICADO
    assert relevamiento.creado_por == coordinador
    assert list(relevamiento.equipo.all()) == [entrevistador]
    assert relevamiento.fecha_fin == datetime.date(2026, 9, 19)


@pytest.mark.django_db
def test_equipo_es_obligatorio(provincias):
    cordoba, _ = provincias
    coordinador = _crear_coordinador(cordoba)

    form = RelevamientoForm(data=_datos_form(cordoba, []), actor=coordinador)

    assert form.is_valid() is False
    assert "equipo" in form.errors


@pytest.mark.django_db
def test_equipo_de_otra_provincia_es_rechazado(provincias):
    cordoba, salta = provincias
    ajeno = _crear_entrevistador(salta, "entrev_salta")
    admin = get_user_model().objects.create_superuser(
        username="admin_nac", email="a@example.com", password="Sisoc12345!"
    )

    form = RelevamientoForm(data=_datos_form(cordoba, [ajeno]), actor=admin)

    assert form.is_valid() is False
    assert "equipo" in form.errors


@pytest.mark.django_db
def test_fecha_fin_no_puede_ser_anterior(provincias):
    cordoba, _ = provincias
    entrevistador = _crear_entrevistador(cordoba, "entrev_fechas")
    coordinador = _crear_coordinador(cordoba)

    form = RelevamientoForm(
        data=_datos_form(
            cordoba, [entrevistador], fecha_inicio="2026-09-19", fecha_fin="2026-09-15"
        ),
        actor=coordinador,
    )

    assert form.is_valid() is False
    assert "fecha_fin" in form.errors


@pytest.mark.django_db
def test_espacio_publico_requiere_area_operativa(provincias):
    cordoba, _ = provincias
    entrevistador = _crear_entrevistador(cordoba, "entrev_area")
    coordinador = _crear_coordinador(cordoba)

    form = RelevamientoForm(
        data=_datos_form(cordoba, [entrevistador], area_operativa=""),
        actor=coordinador,
    )

    assert form.is_valid() is False
    assert "area_operativa" in form.errors


@pytest.mark.django_db
def test_municipio_de_otra_provincia_es_rechazado(provincias):
    cordoba, salta = provincias
    municipio_ajeno = Municipio.objects.create(nombre="Salta Capital", provincia=salta)
    Localidad.objects.create(nombre="Centro", municipio=municipio_ajeno)
    entrevistador = _crear_entrevistador(cordoba, "entrev_geo")
    coordinador = _crear_coordinador(cordoba)

    form = RelevamientoForm(
        data=_datos_form(cordoba, [entrevistador], municipio=municipio_ajeno.id),
        actor=coordinador,
    )

    assert form.is_valid() is False
    assert "municipio" in form.errors


@pytest.mark.django_db
def test_coordinador_solo_ve_su_provincia(provincias):
    cordoba, salta = provincias
    coordinador = _crear_coordinador(cordoba)
    _crear_relevamiento(cordoba, "De Córdoba")
    _crear_relevamiento(salta, "De Salta")

    visibles = apply_relevamientos_scope(get_relevamientos_queryset(), coordinador)

    assert [r.denominacion for r in visibles] == ["De Córdoba"]
    assert [p.nombre for p in get_provincias_para_usuario(coordinador)] == ["Córdoba"]


@pytest.mark.django_db
def test_administrador_ve_todas_las_provincias(provincias):
    cordoba, salta = provincias
    admin = get_user_model().objects.create_superuser(
        username="admin_ve_todo", email="admin@example.com", password="Sisoc12345!"
    )
    _crear_relevamiento(cordoba, "De Córdoba")
    _crear_relevamiento(salta, "De Salta")

    visibles = apply_relevamientos_scope(get_relevamientos_queryset(), admin)

    assert visibles.count() == 2


@pytest.mark.django_db
def test_coordinador_solo_arma_equipo_con_los_suyos(provincias):
    cordoba, salta = provincias
    propio = _crear_entrevistador(cordoba, "propio")
    _crear_entrevistador(salta, "ajeno")
    coordinador = _crear_coordinador(cordoba)

    disponibles = get_entrevistadores_para_usuario(coordinador)

    assert [u.username for u in disponibles] == [propio.username]


@pytest.mark.django_db
def test_baja_es_logica(provincias):
    cordoba, _ = provincias
    relevamiento = _crear_relevamiento(cordoba, "Para borrar")

    delete_relevamiento(relevamiento)

    assert Relevamiento.objects.filter(pk=relevamiento.pk).exists() is False
    assert Relevamiento.all_objects.filter(pk=relevamiento.pk).exists() is True


@pytest.mark.django_db
def test_primer_caso_pasa_a_en_curso(provincias):
    cordoba, _ = provincias
    relevamiento = _crear_relevamiento(cordoba, "Operativo")

    marcar_en_curso(relevamiento)
    relevamiento.refresh_from_db()
    assert relevamiento.estado == Relevamiento.Estado.EN_CURSO

    # No vuelve atrás desde finalizado.
    relevamiento.estado = Relevamiento.Estado.FINALIZADO
    relevamiento.save(update_fields=["estado"])
    marcar_en_curso(relevamiento)
    relevamiento.refresh_from_db()
    assert relevamiento.estado == Relevamiento.Estado.FINALIZADO


def _dar_permisos(user, codenames):
    from django.contrib.auth.models import Permission

    user.user_permissions.add(
        *Permission.objects.filter(
            content_type__app_label="datacalle", codename__in=codenames
        )
    )
    return user


@pytest.mark.django_db
def test_vista_listado_respeta_alcance(client, provincias):
    cordoba, salta = provincias
    coordinador = _dar_permisos(_crear_coordinador(cordoba), ["view_relevamiento"])
    _crear_relevamiento(cordoba, "Visible de Córdoba")
    _crear_relevamiento(salta, "Oculto de Salta")
    client.force_login(coordinador)

    respuesta = client.get("/datacalle/relevamientos/")

    assert respuesta.status_code == 200
    contenido = respuesta.content.decode()
    assert "Visible de Córdoba" in contenido
    assert "Oculto de Salta" not in contenido


@pytest.mark.django_db
def test_vista_detalle_de_otra_provincia_da_404(client, provincias):
    cordoba, salta = provincias
    coordinador = _dar_permisos(_crear_coordinador(cordoba), ["view_relevamiento"])
    ajeno = _crear_relevamiento(salta, "De Salta")
    client.force_login(coordinador)

    respuesta = client.get(f"/datacalle/relevamientos/{ajeno.pk}/")

    assert respuesta.status_code == 404


@pytest.mark.django_db
def test_alta_desde_la_vista_crea_el_operativo(client, provincias):
    cordoba, _ = provincias
    entrevistador = _crear_entrevistador(cordoba, "entrev_vista")
    coordinador = _dar_permisos(
        _crear_coordinador(cordoba), ["add_relevamiento", "view_relevamiento"]
    )
    client.force_login(coordinador)

    respuesta = client.post(
        "/datacalle/relevamientos/crear/",
        data=_datos_form(cordoba, [entrevistador]),
    )

    assert respuesta.status_code == 302
    relevamiento = Relevamiento.objects.get(denominacion="Operativo invierno")
    assert relevamiento.creado_por == coordinador
    assert list(relevamiento.equipo.all()) == [entrevistador]


@pytest.mark.django_db
def test_sin_permiso_no_entra_al_listado(client, provincias):
    cordoba, _ = provincias
    usuario = _crear_coordinador(cordoba, username="sin_permiso")
    client.force_login(usuario)

    respuesta = client.get("/datacalle/relevamientos/")

    assert respuesta.status_code in (302, 403)


@pytest.mark.django_db
def test_pantallas_renderizan_con_diseno(client, provincias):
    cordoba, _ = provincias
    entrevistador = _crear_entrevistador(cordoba, "entrev_diseno")
    coordinador = _dar_permisos(
        _crear_coordinador(cordoba),
        ["view_relevamiento", "add_relevamiento", "change_relevamiento"],
    )
    relevamiento = _crear_relevamiento(cordoba, "Operativo con diseño")
    relevamiento.equipo.add(entrevistador)
    client.force_login(coordinador)

    listado = client.get("/datacalle/relevamientos/")
    assert listado.status_code == 200
    html = listado.content.decode()
    # Resumen por estado, chip de estado y hoja de estilos del módulo.
    assert "dc-stat__valor" in html
    assert "dc-chip--planificado" in html
    assert "custom/css/datacalle.css" in html
    assert "5 días" in html

    detalle = client.get(f"/datacalle/relevamientos/{relevamiento.pk}/")
    assert detalle.status_code == 200
    html = detalle.content.decode()
    assert "dc-seccion__header" in html
    assert "dc-persona__nombre" in html
    # Sin cierre todavía: se muestra el estado vacío, no datos en blanco.
    assert "Todavía sin cerrar" in html

    alta = client.get("/datacalle/relevamientos/crear/")
    assert alta.status_code == 200
    html = alta.content.decode()
    assert "dc-form-seccion__titulo" in html
    assert "Dónde se releva" in html


@pytest.mark.django_db
def test_listado_vacio_muestra_estado_vacio(client, provincias):
    cordoba, _ = provincias
    coordinador = _dar_permisos(_crear_coordinador(cordoba), ["view_relevamiento"])
    client.force_login(coordinador)

    respuesta = client.get("/datacalle/relevamientos/")

    assert respuesta.status_code == 200
    assert "Todavía no hay operativos" in respuesta.content.decode()


@pytest.mark.django_db
def test_cascada_municipio_localidad_no_carga_todo_el_pais(provincias):
    """QA-0008: con una sola provincia en el alcance, ya viene resuelta."""
    cordoba, salta = provincias
    cba_capital = Municipio.objects.create(nombre="Córdoba Capital", provincia=cordoba)
    Municipio.objects.create(nombre="Salta Capital", provincia=salta)
    centro = Localidad.objects.create(nombre="Centro", municipio=cba_capital)
    coordinador = _crear_coordinador(cordoba)

    # Alta en blanco: la provincia está fija, así que los municipios ya salen
    # filtrados por ella y nunca se cargan los del resto del país.
    vacio = RelevamientoForm(actor=coordinador)
    assert [m.nombre for m in vacio.fields["municipio"].queryset] == ["Córdoba Capital"]
    assert vacio.fields["localidades"].queryset.count() == 0

    # Con municipio elegido, sólo sus localidades.
    con_municipio = RelevamientoForm(
        data={"provincia": cordoba.id, "municipio": cba_capital.id},
        actor=coordinador,
    )
    assert [loc.nombre for loc in con_municipio.fields["localidades"].queryset] == [
        centro.nombre
    ]


@pytest.mark.django_db
def test_el_administrador_nacional_arranca_sin_municipios(provincias):
    """Sin provincia definida, no se cargan los miles de municipios del país."""
    cordoba, _ = provincias
    Municipio.objects.create(nombre="Córdoba Capital", provincia=cordoba)
    admin = get_user_model().objects.create_superuser(
        username="admin_sin_prov", email="a@example.com", password="Sisoc12345!"
    )

    form = RelevamientoForm(actor=admin)

    assert form.fields["municipio"].queryset.count() == 0
    assert form.fields["provincia"].disabled is False


@pytest.mark.django_db
def test_provincia_bloqueada_ignora_lo_que_venga_por_post(provincias):
    """QA-0008: el coordinador no puede planificar fuera de su provincia."""
    cordoba, salta = provincias
    entrevistador = _crear_entrevistador(cordoba, "entrev_bloqueo")
    coordinador = _crear_coordinador(cordoba)

    form = RelevamientoForm(data=_datos_form(salta, [entrevistador]), actor=coordinador)

    assert form.fields["provincia"].disabled is True
    assert form.is_valid(), form.errors
    # El POST decía Salta; el campo deshabilitado usa el initial del alcance.
    assert form.cleaned_data["provincia"] == cordoba


@pytest.mark.django_db
def test_edicion_conserva_la_geografia_guardada(provincias):
    cordoba, _ = provincias
    municipio = Municipio.objects.create(nombre="Río Cuarto", provincia=cordoba)
    localidad = Localidad.objects.create(nombre="Río Cuarto", municipio=municipio)
    entrevistador = _crear_entrevistador(cordoba, "entrev_edicion")
    coordinador = _crear_coordinador(cordoba)
    relevamiento = _crear_relevamiento(cordoba, "Con geografía")
    relevamiento.municipio = municipio
    relevamiento.save()
    relevamiento.localidades.add(localidad)
    relevamiento.equipo.add(entrevistador)

    form = RelevamientoForm(instance=relevamiento, actor=coordinador)

    assert municipio in form.fields["municipio"].queryset
    assert localidad in form.fields["localidades"].queryset


@pytest.mark.django_db
def test_operativo_puede_abarcar_varias_localidades(provincias):
    cordoba, _ = provincias
    municipio = Municipio.objects.create(nombre="Córdoba Capital", provincia=cordoba)
    centro = Localidad.objects.create(nombre="Centro", municipio=municipio)
    alberdi = Localidad.objects.create(nombre="Alberdi", municipio=municipio)
    entrevistador = _crear_entrevistador(cordoba, "entrev_zonas")
    coordinador = _crear_coordinador(cordoba)

    form = RelevamientoForm(
        data=_datos_form(
            cordoba,
            [entrevistador],
            municipio=municipio.id,
            localidades=[centro.id, alberdi.id],
        ),
        actor=coordinador,
    )
    assert form.is_valid(), form.errors
    relevamiento = save_relevamiento_from_form(form, user=coordinador)

    assert relevamiento.localidades.count() == 2
    assert (
        relevamiento.zonas == "Alberdi, Centro"
        or relevamiento.zonas == "Centro, Alberdi"
    )


@pytest.mark.django_db
def test_localidad_de_otro_municipio_es_rechazada(provincias):
    cordoba, _ = provincias
    capital = Municipio.objects.create(nombre="Córdoba Capital", provincia=cordoba)
    rio_cuarto = Municipio.objects.create(nombre="Río Cuarto", provincia=cordoba)
    ajena = Localidad.objects.create(nombre="Banda Norte", municipio=rio_cuarto)
    entrevistador = _crear_entrevistador(cordoba, "entrev_zona_ajena")
    coordinador = _crear_coordinador(cordoba)

    form = RelevamientoForm(
        data=_datos_form(
            cordoba,
            [entrevistador],
            municipio=capital.id,
            localidades=[ajena.id],
        ),
        actor=coordinador,
    )

    assert form.is_valid() is False
    assert "localidades" in form.errors


def _caso(relevamiento, **extra):
    from datacalle.models import Encuesta
    from datacalle.services import aplicar_columnas_indexadas

    datos = {
        "relevamiento": relevamiento,
        "estado": Encuesta.Estado.COMPLETA,
        "respuestas": {
            "codigoEntrevistado": "LURO15031980",
            "realizaEntrevista": "si",
            "esCabeceraGrupo": "si",
            "personasObservadas": 2,
            "lugarHallazgo": "espacioPublico",
        },
    }
    datos.update(extra)
    caso = Encuesta(**datos)
    aplicar_columnas_indexadas(caso)
    caso.save()
    return caso


@pytest.mark.django_db
def test_el_operativo_lista_sus_casos(client, provincias):
    cordoba, _ = provincias
    coordinador = _dar_permisos(
        _crear_coordinador(cordoba), ["view_relevamiento", "view_encuesta"]
    )
    relevamiento = _crear_relevamiento(cordoba, "Con casos")
    _caso(relevamiento)
    client.force_login(coordinador)

    respuesta = client.get(f"/datacalle/relevamientos/{relevamiento.pk}/")

    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert "LURO15031980" in html
    assert "Casos relevados" in html
    # Personas observadas sale de los casos cabecera, no de contar casos.
    assert "Personas observadas" in html


@pytest.mark.django_db
def test_detalle_del_caso_muestra_etiquetas_legibles(client, provincias):
    cordoba, _ = provincias
    coordinador = _dar_permisos(
        _crear_coordinador(cordoba), ["view_relevamiento", "view_encuesta"]
    )
    relevamiento = _crear_relevamiento(cordoba, "Con casos")
    caso = _caso(relevamiento)
    client.force_login(coordinador)

    respuesta = client.get(f"/datacalle/casos/{caso.pk}/")

    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    # El código de catálogo se muestra con su etiqueta, no crudo.
    assert "Espacio público" in html


@pytest.mark.django_db
def test_no_veo_casos_de_otra_provincia(client, provincias):
    cordoba, salta = provincias
    coordinador = _dar_permisos(
        _crear_coordinador(cordoba), ["view_relevamiento", "view_encuesta"]
    )
    ajeno = _caso(_crear_relevamiento(salta, "De Salta"))
    client.force_login(coordinador)

    respuesta = client.get(f"/datacalle/casos/{ajeno.pk}/")

    assert respuesta.status_code == 404


@pytest.mark.django_db
def test_equipo_y_dispositivos_se_acotan_a_la_provincia_elegida(provincias):
    """QA-0010 y QA-0013: el administrador nacional tampoco ve todo el país."""
    from datacalle.services import (
        get_dispositivos_para_provincia,
        get_entrevistadores_para_provincia,
    )

    cordoba, salta = provincias
    propio = _crear_entrevistador(cordoba, "entrev_cba_qa")
    _crear_entrevistador(salta, "entrev_salta_qa")
    admin = get_user_model().objects.create_superuser(
        username="admin_qa", email="admin_qa@example.com", password="Sisoc12345!"
    )

    assert [
        u.username for u in get_entrevistadores_para_provincia(admin, cordoba.id)
    ] == [propio.username]
    # Sin provincia no se ofrece nada, en vez de ofrecer el padrón entero.
    assert get_entrevistadores_para_provincia(admin, None).count() == 0
    assert get_dispositivos_para_provincia(admin, None).count() == 0


@pytest.mark.django_db
def test_el_selector_de_equipo_solo_trae_la_provincia_del_operativo(provincias):
    cordoba, salta = provincias
    propio = _crear_entrevistador(cordoba, "propio_qa")
    _crear_entrevistador(salta, "ajeno_qa")
    admin = get_user_model().objects.create_superuser(
        username="admin_selector", email="a2@example.com", password="Sisoc12345!"
    )

    form = RelevamientoForm(data={"provincia": cordoba.id}, actor=admin)

    assert [u.username for u in form.fields["equipo"].queryset] == [propio.username]


@pytest.mark.django_db
def test_endpoint_de_relevadores_respeta_el_alcance(client, provincias):
    """El endpoint de la cascada no puede filtrar datos de otra provincia."""
    cordoba, salta = provincias
    _crear_entrevistador(cordoba, "visible_qa")
    _crear_entrevistador(salta, "invisible_qa")
    coordinador = _dar_permisos(_crear_coordinador(cordoba), ["view_relevamiento"])
    client.force_login(coordinador)

    propia = client.get(f"/datacalle/ajax/relevadores/?provincia_id={cordoba.id}")
    ajena = client.get(f"/datacalle/ajax/relevadores/?provincia_id={salta.id}")

    assert propia.status_code == 200
    assert len(propia.json()) == 1
    # Pide otra provincia por URL: el alcance del coordinador lo deja vacío.
    assert ajena.json() == []


@pytest.mark.django_db
def test_endpoint_de_dispositivos_responde_json(client, provincias):
    cordoba, _ = provincias
    coordinador = _dar_permisos(_crear_coordinador(cordoba), ["view_relevamiento"])
    client.force_login(coordinador)

    respuesta = client.get(f"/datacalle/ajax/dispositivos/?provincia_id={cordoba.id}")

    assert respuesta.status_code == 200
    assert respuesta.json() == []


def _coordinador_con_scope(provincia, username, municipio=None):
    """Coordinador con alcance a provincia completa o acotado a un municipio."""
    user = get_user_model().objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="Sisoc12345!",
    )
    user.profile.es_usuario_provincial = True
    user.profile.save()
    user.profile.territorial_scopes.create(provincia=provincia, municipio=municipio)
    return user


@pytest.mark.django_db
def test_municipios_de_un_coordinador_con_provincia_completa(provincias):
    from datacalle.services import get_municipios_para_usuario

    cordoba, _ = provincias
    Municipio.objects.create(nombre="Córdoba Capital", provincia=cordoba)
    Municipio.objects.create(nombre="Río Cuarto", provincia=cordoba)
    coordinador = _coordinador_con_scope(cordoba, "coord_prov_completa")

    municipios = get_municipios_para_usuario(coordinador, cordoba.id)

    assert [m.nombre for m in municipios] == ["Córdoba Capital", "Río Cuarto"]


@pytest.mark.django_db
def test_municipios_de_un_coordinador_acotado_a_un_municipio(provincias):
    """QA-0008: si el alcance baja a municipio, el selector no puede ofrecer la provincia."""
    from datacalle.services import get_municipios_para_usuario

    cordoba, _ = provincias
    capital = Municipio.objects.create(nombre="Córdoba Capital", provincia=cordoba)
    Municipio.objects.create(nombre="Río Cuarto", provincia=cordoba)
    coordinador = _coordinador_con_scope(cordoba, "coord_municipal", municipio=capital)

    municipios = get_municipios_para_usuario(coordinador, cordoba.id)

    assert [m.nombre for m in municipios] == ["Córdoba Capital"]


@pytest.mark.django_db
def test_municipios_de_una_provincia_fuera_del_alcance(provincias):
    """Provincia ausente del mapa de alcance: nada, no la provincia entera."""
    from datacalle.services import get_municipios_para_usuario

    cordoba, salta = provincias
    Municipio.objects.create(nombre="Salta Capital", provincia=salta)
    coordinador = _coordinador_con_scope(cordoba, "coord_ajeno")

    assert get_municipios_para_usuario(coordinador, salta.id).count() == 0


@pytest.mark.django_db
def test_municipios_de_un_usuario_sin_restriccion_territorial(provincias):
    """Superusuario o no-territorial: la provincia entera, sin mapa de alcance."""
    from datacalle.services import get_municipios_para_usuario

    cordoba, _ = provincias
    Municipio.objects.create(nombre="Córdoba Capital", provincia=cordoba)
    Municipio.objects.create(nombre="Río Cuarto", provincia=cordoba)
    admin = get_user_model().objects.create_superuser(
        username="admin_municipios", email="am@example.com", password="Sisoc12345!"
    )

    municipios = get_municipios_para_usuario(admin, cordoba.id)

    assert [m.nombre for m in municipios] == ["Córdoba Capital", "Río Cuarto"]


@pytest.mark.django_db
def test_municipios_sin_provincia_no_carga_el_pais(provincias):
    from datacalle.services import get_municipios_para_usuario

    cordoba, _ = provincias
    Municipio.objects.create(nombre="Córdoba Capital", provincia=cordoba)
    admin = get_user_model().objects.create_superuser(
        username="admin_sin_provincia", email="asp@example.com", password="Sisoc12345!"
    )

    assert get_municipios_para_usuario(admin, None).count() == 0


@pytest.mark.django_db
def test_qa_0020_el_coordinador_cierra_desde_el_backoffice(client, provincias):
    """QA-0020: contraparte de haberle sacado el cierre a la app."""
    cordoba, _ = provincias
    coordinador = _dar_permisos(
        _crear_coordinador(cordoba), ["change_relevamiento", "view_relevamiento"]
    )
    relevamiento = _crear_relevamiento(cordoba, "Para cerrar")
    client.force_login(coordinador)

    respuesta = client.post(f"/datacalle/relevamientos/{relevamiento.pk}/cerrar/")

    assert respuesta.status_code == 302
    relevamiento.refresh_from_db()
    assert relevamiento.estado == Relevamiento.Estado.FINALIZADO
    assert relevamiento.cerrado_por == coordinador


@pytest.mark.django_db
def test_qa_0020_cerrar_por_get_no_cierra_nada(client, provincias):
    """Un link no puede cerrar un operativo: sólo POST."""
    cordoba, _ = provincias
    coordinador = _dar_permisos(
        _crear_coordinador(cordoba), ["change_relevamiento", "view_relevamiento"]
    )
    relevamiento = _crear_relevamiento(cordoba, "No cerrar por GET")
    client.force_login(coordinador)

    respuesta = client.get(f"/datacalle/relevamientos/{relevamiento.pk}/cerrar/")

    assert respuesta.status_code == 405
    relevamiento.refresh_from_db()
    assert relevamiento.estado != Relevamiento.Estado.FINALIZADO


@pytest.mark.django_db
def test_qa_0020_sin_permiso_de_cambio_no_se_cierra(client, provincias):
    cordoba, _ = provincias
    mirón = _dar_permisos(
        _crear_coordinador(cordoba, "solo_lectura"), ["view_relevamiento"]
    )
    relevamiento = _crear_relevamiento(cordoba, "Ajeno al cierre")
    client.force_login(mirón)

    respuesta = client.post(f"/datacalle/relevamientos/{relevamiento.pk}/cerrar/")

    assert respuesta.status_code in (302, 403)
    relevamiento.refresh_from_db()
    assert relevamiento.estado != Relevamiento.Estado.FINALIZADO
