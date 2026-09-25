"""API REST de Celiaquia.

El foco esta puesto en lo que puede salir mal de forma silenciosa:
el alcance por rol/territorio y que las escrituras pasen por los services.
"""

from datetime import date

import pytest
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from celiaquia.models import (
    EstadoExpediente,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
    ProvinciaCupo,
)
from ciudadanos.models import Ciudadano
from core.models import Localidad, Municipio, Provincia
from users.models import Profile, ProfileTerritorialScope

pytestmark = pytest.mark.django_db


def _grant(user, codename, model, name=None):
    content_type = ContentType.objects.get_for_model(model)
    perm, _ = Permission.objects.get_or_create(
        codename=codename,
        content_type=content_type,
        defaults={"name": name or codename},
    )
    user.user_permissions.add(perm)


def _coordinador(username="coord_api"):
    user = User.objects.create_user(username=username, password="pass")
    _grant(user, "view_expediente", Expediente)
    _grant(user, "role_coordinadorceliaquia", User, name="Coordinador Celiaquia")
    return user


def _tecnico(username="tecnico_api"):
    user = User.objects.create_user(username=username, password="pass")
    _grant(user, "view_expediente", Expediente)
    _grant(user, "role_tecnicoceliaquia", User, name="Tecnico Celiaquia")
    return user


def _provincial(username, provincia):
    user = User.objects.create_user(username=username, password="pass")
    _grant(user, "view_expediente", Expediente)
    _grant(user, "role_provinciaceliaquia", User, name="Provincia Celiaquia")
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.es_usuario_provincial = True
    profile.save()
    ProfileTerritorialScope.objects.create(profile=profile, provincia=provincia)
    return user


@pytest.fixture
def territorio():
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Tolosa", municipio=municipio)
    return provincia, municipio, localidad


@pytest.fixture
def otro_territorio():
    provincia = Provincia.objects.create(nombre="Cordoba")
    municipio = Municipio.objects.create(nombre="Capital", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Centro", municipio=municipio)
    return provincia, municipio, localidad


def _expediente_con_legajo(owner, territorio, doc, sufijo):
    provincia, municipio, localidad = territorio
    estado_exp, _ = EstadoExpediente.objects.get_or_create(nombre="EN_CARGA")
    estado_legajo, _ = EstadoLegajo.objects.get_or_create(nombre="CARGADO")
    expediente = Expediente.objects.create(
        usuario_provincia=owner, estado=estado_exp, numero_expediente=f"EX-{sufijo}"
    )
    ciudadano = Ciudadano.objects.create(
        apellido="Perez",
        nombre="Ana",
        documento=doc,
        fecha_nacimiento=date(1990, 1, 1),
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
    )
    legajo = ExpedienteCiudadano.objects.create(
        expediente=expediente, ciudadano=ciudadano, estado=estado_legajo
    )
    return expediente, legajo


# --- Autenticacion ---------------------------------------------------------


def test_la_api_exige_autenticacion(client):
    response = client.get(reverse("celiaquia-expediente-list"))

    assert response.status_code in (401, 403)


# --- Alcance: lo que mas importa -------------------------------------------


def test_provincial_no_ve_expedientes_de_otra_provincia(
    client, territorio, otro_territorio
):
    propio_owner = _provincial("prov_bsas", territorio[0])
    ajeno_owner = _provincial("prov_cba", otro_territorio[0])
    propio, _ = _expediente_con_legajo(propio_owner, territorio, "30111111", "A")
    ajeno, _ = _expediente_con_legajo(ajeno_owner, otro_territorio, "30222222", "B")
    client.force_login(propio_owner)

    response = client.get(reverse("celiaquia-expediente-list"))
    ids = [fila["id"] for fila in response.json()["results"]]

    assert response.status_code == 200
    assert propio.pk in ids
    assert ajeno.pk not in ids


def test_provincial_no_puede_leer_el_detalle_ajeno(client, territorio, otro_territorio):
    propio_owner = _provincial("prov_bsas_detalle", territorio[0])
    ajeno_owner = _provincial("prov_cba_detalle", otro_territorio[0])
    ajeno, _ = _expediente_con_legajo(ajeno_owner, otro_territorio, "30333333", "C")
    client.force_login(propio_owner)

    response = client.get(
        reverse("celiaquia-expediente-detail", kwargs={"pk": ajeno.pk})
    )

    assert response.status_code == 404


def test_tecnico_solo_ve_los_expedientes_asignados(client, territorio):
    owner = _provincial("prov_asignado", territorio[0])
    asignado, _ = _expediente_con_legajo(owner, territorio, "30444444", "D")
    _expediente_con_legajo(owner, territorio, "30555555", "E")
    tecnico = _tecnico()
    asignado.asignaciones_tecnicos.create(tecnico=tecnico, activa=True)
    client.force_login(tecnico)

    response = client.get(reverse("celiaquia-expediente-list"))
    ids = [fila["id"] for fila in response.json()["results"]]

    assert ids == [asignado.pk]


def test_coordinador_ve_todos(client, territorio, otro_territorio):
    owner_a = _provincial("prov_a", territorio[0])
    owner_b = _provincial("prov_b", otro_territorio[0])
    uno, _ = _expediente_con_legajo(owner_a, territorio, "30666666", "F")
    dos, _ = _expediente_con_legajo(owner_b, otro_territorio, "30777777", "G")
    client.force_login(_coordinador())

    response = client.get(reverse("celiaquia-expediente-list"))
    ids = [fila["id"] for fila in response.json()["results"]]

    assert {uno.pk, dos.pk} <= set(ids)


def test_los_legajos_heredan_el_alcance_del_expediente(
    client, territorio, otro_territorio
):
    propio_owner = _provincial("prov_leg", territorio[0])
    ajeno_owner = _provincial("prov_leg_ajeno", otro_territorio[0])
    _, legajo_propio = _expediente_con_legajo(propio_owner, territorio, "30888888", "H")
    _, legajo_ajeno = _expediente_con_legajo(
        ajeno_owner, otro_territorio, "30999999", "I"
    )
    client.force_login(propio_owner)

    response = client.get(reverse("celiaquia-legajo-list"))
    ids = [fila["id"] for fila in response.json()["results"]]

    assert legajo_propio.pk in ids
    assert legajo_ajeno.pk not in ids


# --- Contenido de la respuesta ---------------------------------------------


def test_el_expediente_no_expone_archivos_internos_ni_usuarios(client, territorio):
    owner = _provincial("prov_campos", territorio[0])
    expediente, _ = _expediente_con_legajo(owner, territorio, "31000000", "J")
    client.force_login(owner)

    fila = client.get(
        reverse("celiaquia-expediente-detail", kwargs={"pk": expediente.pk})
    ).json()

    assert fila["numero_expediente"] == "EX-J"
    assert fila["estado"] == "EN_CARGA"
    assert fila["legajos_total"] == 1
    # Rutas de archivos y datos de usuario no salen de la aplicacion.
    for prohibido in (
        "excel_masivo",
        "cruce_excel",
        "documento",
        "excel_masivo_cargado_por",
    ):
        assert prohibido not in fila
    assert set(fila["usuario_provincia"]) == {"id", "nombre"}


def test_sub_recurso_legajos_del_expediente(client, territorio):
    owner = _provincial("prov_sub", territorio[0])
    expediente, legajo = _expediente_con_legajo(owner, territorio, "31111111", "K")
    client.force_login(owner)

    response = client.get(
        reverse("celiaquia-expediente-legajos", kwargs={"pk": expediente.pk})
    )
    datos = response.json()
    filas = datos["results"] if isinstance(datos, dict) else datos

    assert response.status_code == 200
    assert [fila["id"] for fila in filas] == [legajo.pk]
    assert filas[0]["ciudadano"] == "Perez Ana"


def test_filtra_expedientes_por_estado(client, territorio):
    owner = _provincial("prov_filtro", territorio[0])
    expediente, _ = _expediente_con_legajo(owner, territorio, "31222222", "L")
    client.force_login(owner)

    con_match = client.get(
        reverse("celiaquia-expediente-list"), {"estado": "EN_CARGA"}
    ).json()["results"]
    sin_match = client.get(
        reverse("celiaquia-expediente-list"), {"estado": "CERRADO"}
    ).json()["results"]

    assert [fila["id"] for fila in con_match] == [expediente.pk]
    assert sin_match == []


# --- Acciones: delegan en los services -------------------------------------


def test_asignar_tecnico_requiere_coordinacion(client, territorio):
    owner = _provincial("prov_asignar", territorio[0])
    expediente, _ = _expediente_con_legajo(owner, territorio, "31333333", "M")
    tecnico = _tecnico("tecnico_destino")
    client.force_login(owner)

    response = client.post(
        reverse("celiaquia-expediente-asignar-tecnico", kwargs={"pk": expediente.pk}),
        {"tecnico_id": tecnico.pk},
        content_type="application/json",
    )

    assert response.status_code == 403


def test_asignar_tecnico_delega_en_el_service(client, territorio, mocker):
    owner = _provincial("prov_asignar_ok", territorio[0])
    expediente, _ = _expediente_con_legajo(owner, territorio, "31444444", "N")
    tecnico = _tecnico("tecnico_ok")
    asignar = mocker.patch("celiaquia.api_views.ExpedienteService.asignar_tecnico")
    client.force_login(_coordinador("coord_asignar"))

    response = client.post(
        reverse("celiaquia-expediente-asignar-tecnico", kwargs={"pk": expediente.pk}),
        {"tecnico_id": tecnico.pk},
        content_type="application/json",
    )

    assert response.status_code == 200
    assert asignar.call_count == 1
    argumentos = asignar.call_args.args
    assert argumentos[0].pk == expediente.pk
    assert argumentos[1].pk == tecnico.pk


def test_procesar_delega_en_el_service(client, territorio, mocker):
    owner = _provincial("prov_procesar", territorio[0])
    expediente, _ = _expediente_con_legajo(owner, territorio, "31555555", "O")
    procesar = mocker.patch("celiaquia.api_views.ExpedienteService.procesar_expediente")
    client.force_login(owner)

    response = client.post(
        reverse("celiaquia-expediente-procesar", kwargs={"pk": expediente.pk})
    )

    assert response.status_code == 200
    assert procesar.call_count == 1
    assert response.json()["expediente"]["id"] == expediente.pk


def test_el_error_del_service_vuelve_como_400(client, territorio, mocker):
    from django.core.exceptions import ValidationError as DjangoValidationError

    owner = _provincial("prov_error", territorio[0])
    expediente, _ = _expediente_con_legajo(owner, territorio, "31666666", "P")
    mocker.patch(
        "celiaquia.api_views.ExpedienteService.confirmar_envio",
        side_effect=DjangoValidationError("Faltan archivos en 3 legajos."),
    )
    client.force_login(owner)

    response = client.post(
        reverse("celiaquia-expediente-confirmar-envio", kwargs={"pk": expediente.pk})
    )

    assert response.status_code == 400
    assert "Faltan archivos en 3 legajos." in str(response.json()["detail"])


def test_solicitar_subsanacion_delega_en_el_service(client, territorio, mocker):
    owner = _provincial("prov_subsanar", territorio[0])
    _, legajo = _expediente_con_legajo(owner, territorio, "31777777", "Q")
    solicitar = mocker.patch("celiaquia.api_views.LegajoService.solicitar_subsanacion")
    client.force_login(owner)

    response = client.post(
        reverse("celiaquia-legajo-solicitar-subsanacion", kwargs={"pk": legajo.pk}),
        {"motivo": "Falta el certificado medico."},
        content_type="application/json",
    )

    assert response.status_code == 200
    assert solicitar.call_args.args[0].pk == legajo.pk
    assert solicitar.call_args.args[1] == "Falta el certificado medico."


def test_solicitar_subsanacion_valida_la_entrada(client, territorio):
    owner = _provincial("prov_subsanar_mal", territorio[0])
    _, legajo = _expediente_con_legajo(owner, territorio, "31888888", "R")
    client.force_login(owner)

    response = client.post(
        reverse("celiaquia-legajo-solicitar-subsanacion", kwargs={"pk": legajo.pk}),
        {},
        content_type="application/json",
    )

    assert response.status_code == 400
    assert "motivo" in response.json()


# --- Catalogos y cupos -----------------------------------------------------


def test_los_catalogos_se_listan_sin_paginar(client, territorio):
    EstadoExpediente.objects.get_or_create(nombre="EN_CARGA")
    EstadoExpediente.objects.get_or_create(nombre="CERRADO")
    client.force_login(_coordinador("coord_catalogo"))

    datos = client.get(reverse("celiaquia-estado-expediente-list")).json()

    assert isinstance(datos, list)
    assert {"EN_CARGA", "CERRADO"} <= {fila["nombre"] for fila in datos}


def test_cupo_calcula_los_disponibles(client, territorio):
    provincia = territorio[0]
    ProvinciaCupo.objects.create(provincia=provincia, total_asignado=100, usados=30)
    client.force_login(_coordinador("coord_cupo"))

    fila = client.get(reverse("celiaquia-cupo-list")).json()["results"][0]

    assert fila["provincia"] == "Buenos Aires"
    assert fila["total_asignado"] == 100
    assert fila["usados"] == 30
    assert fila["disponibles"] == 70
