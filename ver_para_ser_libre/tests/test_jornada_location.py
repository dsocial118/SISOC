from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from core.models import Localidad, Municipio, Provincia
from ver_para_ser_libre.forms import ItinerarioVPSLForm, JornadaVPSLForm
from ver_para_ser_libre.models import (
    ChecklistJornadaVPSL,
    EstadoEvaluacionVPSL,
    EstadoItinerario,
    EstadoJornada,
    ItinerarioVPSL,
    JornadaVPSL,
    VehiculoVPSL,
)
from ver_para_ser_libre.services import map_location, workflow


pytestmark = pytest.mark.django_db

MAP_URL = "https://www.google.com/maps/search/" "?api=1&query=-34.603700%2C-58.381600"
STREET_VIEW_URL = (
    "https://www.google.com/maps/@?api=1&map_action=pano"
    "&viewpoint=-34.631040%2C-58.465853"
)


def _crear_itinerario(*, estado=EstadoItinerario.APROBADO):
    return ItinerarioVPSL.objects.create(
        provincia=Provincia.objects.create(nombre="Buenos Aires"),
        fecha_inicio=date(2026, 9, 1),
        fecha_fin=date(2026, 9, 30),
        referente_nombre="Referente",
        referente_telefono="11111111",
        referente_email="referente@example.com",
        carta_archivo=SimpleUploadedFile("carta.pdf", b"contenido"),
        carta_archivo_estado=EstadoEvaluacionVPSL.APROBADO,
        estado=estado,
    )


def test_resolver_extrae_coordenadas_de_busqueda_canonica():
    location = map_location.resolve_google_maps_location(MAP_URL)

    assert location.latitude == Decimal("-34.603700")
    assert location.longitude == Decimal("-58.381600")
    assert location.address == ""
    assert location.query == "-34.603700,-58.381600"


def test_resolver_acepta_street_view_oficial_con_viewpoint():
    location = map_location.resolve_google_maps_location(STREET_VIEW_URL)

    assert location.original_url == STREET_VIEW_URL
    assert location.latitude == Decimal("-34.631040")
    assert location.longitude == Decimal("-58.465853")


def test_resolver_convierte_coordenadas_con_espacios_a_url_canonica():
    location = map_location.resolve_google_maps_location("-34.631040, -58.465853")

    assert location.original_url == (
        "https://www.google.com/maps/search/" "?api=1&query=-34.631040%2C-58.465853"
    )
    assert location.latitude == Decimal("-34.631040")
    assert location.longitude == Decimal("-58.465853")


def test_resolver_descarta_parametros_adicionales_antes_de_extraer_coordenadas():
    location = map_location.resolve_google_maps_location(
        "https://www.google.com/maps/search/"
        "?noise=10,20&api=1&query=-34.603700%2C-58.381600&extra=30,40"
    )

    assert location.original_url == MAP_URL
    assert location.latitude == Decimal("-34.603700")
    assert location.longitude == Decimal("-58.381600")


@pytest.mark.parametrize(
    "url",
    [
        "http://maps.app.goo.gl/abc",
        "https://maps.app.goo.gl.ejemplo.test/abc",
        "https://usuario@maps.app.goo.gl/abc",
        "https://127.0.0.1/maps",
        "https://www.google.com/maps/place/Av.+Siempre+Viva+742/"
        "@-34.603700,-58.381600,17z",
        "https://maps.google.com/?q=-34.603700,-58.381600",
        "https://www.google.com/maps/search/?api=1&query=Av.+Siempre+Viva+742",
        "https://maps.app.goo.gl/" + ("a" * 600),
    ],
)
def test_resolver_rechaza_urls_no_permitidas(url):
    with pytest.raises(ValidationError):
        map_location.resolve_google_maps_location(url)


def test_resolver_link_corto_usa_destino_validado(monkeypatch):
    short_url = "https://maps.app.goo.gl/GVuUzZfkRUEAWkdT8"
    destination = "https://www.google.com/maps/search/-34.602293,+-58.397165?entry=tts"
    monkeypatch.setattr(
        map_location, "_resolve_short_url", lambda *_args, **_kwargs: destination
    )

    location = map_location.resolve_google_maps_location(short_url)

    assert location.original_url == short_url
    assert location.latitude == Decimal("-34.602293")
    assert location.longitude == Decimal("-58.397165")
    assert location.address == ""


def test_formularios_reemplazan_sede_tentativa_por_ubicacion_de_jornada():
    itinerario = _crear_itinerario()
    vehiculo_1 = VehiculoVPSL.objects.create(nombre="Vehiculo 1", orden=1)
    vehiculo_2 = VehiculoVPSL.objects.create(nombre="Vehiculo 2", orden=2)
    localidad = Localidad.objects.create(
        nombre="La Plata",
        municipio=Municipio.objects.create(
            nombre="La Plata",
            provincia=itinerario.provincia,
        ),
    )

    assert "sedes" not in ItinerarioVPSLForm().fields
    assert "localidad_filtro" not in ItinerarioVPSLForm().fields

    form_data = {
        "fecha": "2026-09-15",
        "sede": "Escuela de prueba",
        "localidad": localidad.pk,
        "ubicacion_url": "-34.603700, -58.381600",
        "direccion": "Av. Siempre Viva 742",
        "vehiculos": [str(vehiculo_1.pk), str(vehiculo_2.pk)],
        "horario_inicio": "09:00",
        "horario_fin": "18:00",
        "referente_dni": "",
        "referente_sexo": "",
        "referente_telefono": "",
        "observaciones": "",
    }
    form = JornadaVPSLForm(data=form_data, itinerario=itinerario)

    assert "referente_email" not in form.fields
    assert form.is_valid(), form.errors
    jornada = form.save(commit=False)
    jornada.itinerario = itinerario
    jornada.save()
    form.save_m2m()
    assert jornada.sede_vpsl is None
    assert jornada.localidad == localidad
    assert jornada.direccion == "Av. Siempre Viva 742"
    assert jornada.ubicacion_url == MAP_URL
    assert jornada.latitud == Decimal("-34.603700")
    assert jornada.longitud == Decimal("-58.381600")
    assert list(jornada.vehiculos.all()) == [vehiculo_1, vehiculo_2]
    assert jornada.get_vehiculo_display() == "Vehiculo 1, Vehiculo 2"

    form_data["vehiculos"] = [str(vehiculo_2.pk)]
    update_form = JornadaVPSLForm(
        data=form_data,
        instance=jornada,
        itinerario=itinerario,
    )
    assert update_form.is_valid(), update_form.errors
    jornada = update_form.save()
    assert list(jornada.vehiculos.all()) == [vehiculo_2]
    assert jornada.get_vehiculo_display() == "Vehiculo 2"


def test_buscar_ubicacion_requiere_permiso_y_devuelve_preview(client):
    url = reverse("vpsl_ubicacion_buscar")
    user = get_user_model().objects.create_user(username="sin-permiso")
    client.force_login(user)
    assert client.post(url, {"ubicacion_url": MAP_URL}).status_code == 403

    user.is_superuser = True
    user.is_staff = True
    user.save(update_fields=["is_superuser", "is_staff"])
    response = client.post(url, {"ubicacion_url": MAP_URL})

    assert response.status_code == 200
    assert response.json()["ubicacion_url"] == MAP_URL
    assert response.json()["query"] == "-34.603700,-58.381600"
    assert response.json()["direccion"] == ""


def test_buscar_ubicacion_limita_intentos_por_usuario_e_ip(client, monkeypatch):
    user = get_user_model().objects.create_superuser(username="vpsl-map-rate-limit")
    client.force_login(user)
    monkeypatch.setattr(
        "ver_para_ser_libre.views.hit_rate_limit",
        lambda **_kwargs: True,
    )

    response = client.post(
        reverse("vpsl_ubicacion_buscar"),
        {"ubicacion_url": MAP_URL},
        REMOTE_ADDR="203.0.113.10",
    )

    assert response.status_code == 429
    assert response["Retry-After"] == "60"
    assert response.json()["success"] is False


def test_jornada_form_y_detalle_muestran_busqueda_preview_y_enlace(client):
    itinerario = _crear_itinerario()
    localidad = Localidad.objects.create(
        nombre="Quilmes",
        municipio=Municipio.objects.create(
            nombre="Quilmes",
            provincia=itinerario.provincia,
        ),
    )
    user = get_user_model().objects.create_superuser(username="vpsl-ubicacion")
    client.force_login(user)

    form_response = client.get(
        reverse("vpsl_jornada_create", kwargs={"itinerario_pk": itinerario.pk})
    )
    content = form_response.content.decode()
    assert form_response.status_code == 200
    assert 'id="id_sede"' in content
    assert 'id="id_localidad"' in content
    assert 'id="id_referente_email"' not in content
    assert 'id="id_ubicacion_url"' in content
    assert 'id="buscar-ubicacion"' in content
    assert 'id="ubicacion-mapa"' in content
    assert 'id="id_sede_vpsl"' not in content

    jornada = JornadaVPSL.objects.create(
        itinerario=itinerario,
        fecha=date(2026, 9, 15),
        sede="Escuela de prueba",
        localidad=localidad,
        direccion="Av. Siempre Viva 742",
        ubicacion_url=MAP_URL,
        latitud=Decimal("-34.603700"),
        longitud=Decimal("-58.381600"),
    )
    detail_response = client.get(
        reverse("vpsl_jornada_detail", kwargs={"pk": jornada.pk})
    )
    detail_content = detail_response.content.decode()
    assert detail_response.status_code == 200
    assert "Abrir en Google Maps" in detail_content
    assert "-34.603700%2C-58.381600" in detail_content

    itinerario_response = client.get(
        reverse("vpsl_itinerario_detail", kwargs={"pk": itinerario.pk})
    )
    assert itinerario_response.status_code == 200
    assert "Quilmes" in itinerario_response.content.decode()


def test_exportaciones_incluyen_coordenadas_de_la_sede(client):
    itinerario = _crear_itinerario()
    jornada = JornadaVPSL.objects.create(
        itinerario=itinerario,
        fecha=date(2026, 9, 15),
        sede="Escuela exportable",
        ubicacion_url=MAP_URL,
        latitud=Decimal("-34.603700"),
        longitud=Decimal("-58.381600"),
    )
    user = get_user_model().objects.create_superuser(username="vpsl-export-location")
    client.force_login(user)

    itinerario_response = client.get(
        reverse("vpsl_itinerario_export", kwargs={"pk": itinerario.pk})
    )
    itinerario_csv = b"".join(itinerario_response.streaming_content).decode("utf-8")
    jornada_response = client.get(
        reverse("vpsl_jornada_export", kwargs={"pk": jornada.pk})
    )
    jornada_csv = b"".join(jornada_response.streaming_content).decode("utf-8")

    assert itinerario_response.status_code == 200
    assert jornada_response.status_code == 200
    assert "Ubicacion sede" in itinerario_csv
    assert "Ubicacion sede" in jornada_csv
    assert "-34.603700,-58.381600" in itinerario_csv
    assert "-34.603700,-58.381600" in jornada_csv


def test_itinerario_se_aprueba_sin_sedes_y_checklist_pertenece_a_jornada():
    itinerario = _crear_itinerario(estado=EstadoItinerario.PRESENTADO)
    workflow.aprobar_itinerario(itinerario)
    itinerario.refresh_from_db()
    assert itinerario.estado == EstadoItinerario.APROBADO
    assert not itinerario.sedes.exists()

    jornada = JornadaVPSL.objects.create(
        itinerario=itinerario,
        fecha=date(2026, 9, 15),
        sede="Escuela de prueba",
        direccion="Av. Siempre Viva 742",
        ubicacion_url=MAP_URL,
        latitud=Decimal("-34.603700"),
        longitud=Decimal("-58.381600"),
    )
    for item in workflow.JORNADA_CHECKLIST_REQUERIDO:
        ChecklistJornadaVPSL.objects.create(
            jornada=jornada,
            item=item,
            cumple=True,
            critico=True,
        )

    workflow.sincronizar_estado_checklist_jornada(jornada)
    jornada.refresh_from_db()
    assert jornada.estado == EstadoJornada.HABILITADA


def test_guardar_checklist_completo_habilita_en_un_solo_envio(client):
    itinerario = _crear_itinerario()
    jornada = JornadaVPSL.objects.create(
        itinerario=itinerario,
        fecha=date(2026, 9, 15),
        sede="Escuela con checklist",
    )
    user = get_user_model().objects.create_superuser(username="vpsl-checklist-auto")
    client.force_login(user)
    data = {f"{item}_cumple": "true" for item in workflow.JORNADA_CHECKLIST_REQUERIDO}

    response = client.post(
        reverse("vpsl_checklist_create", kwargs={"jornada_pk": jornada.pk}),
        data,
    )

    jornada.refresh_from_db()
    assert response.status_code == 302
    assert jornada.estado == EstadoJornada.HABILITADA
    detail = client.get(reverse("vpsl_jornada_detail", kwargs={"pk": jornada.pk}))
    assert "Habilitar" not in detail.content.decode()
