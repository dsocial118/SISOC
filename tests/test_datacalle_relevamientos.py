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
