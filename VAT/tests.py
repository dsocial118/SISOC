import pytest
from django.contrib.auth.models import Group, User
from django.urls import reverse

from VAT.models import (
	AutoridadInstitucional,
	Centro,
	InstitucionContacto,
	InstitucionIdentificadorHist,
	InstitucionUbicacion,
)
from core.models import Localidad, Municipio, Provincia


@pytest.fixture
def vat_geo_data(db):
	provincia = Provincia.objects.create(nombre="Buenos Aires")
	municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
	localidad = Localidad.objects.create(nombre="Tolosa", municipio=municipio)
	return provincia, municipio, localidad


@pytest.fixture
def vat_referente_user(db):
	group, _ = Group.objects.get_or_create(name="ReferenteCentroVAT")
	user = User.objects.create_user(username="referente-vat", password="test1234")
	user.groups.add(group)
	return user


@pytest.fixture
def vat_admin_client(client, db):
	user = User.objects.create_superuser(
		username="admin-vat",
		email="admin@vat.test",
		password="test1234",
	)
	client.force_login(user)
	return client


def _build_centro_payload(referente_user, provincia, municipio, localidad, **overrides):
	payload = {
		"nombre": "Centro de Formación 401",
		"codigo": "500144900",
		"provincia": str(provincia.pk),
		"municipio": str(municipio.pk),
		"localidad": str(localidad.pk),
		"calle": "7",
		"numero": "1234",
		"domicilio_actividad": "Calle 7 N° 1234",
		"codigo_postal": "1900",
		"lote": "12",
		"manzana": "B",
		"entre_calles": "45 y 46",
		"telefono": "221-4000000",
		"celular": "221-5000000",
		"correo": "institucion@vat.test",
		"sitio_web": "https://vat.test",
		"nombre_referente": "Ana",
		"apellido_referente": "Pérez",
		"autoridad_dni": "30111222",
		"telefono_referente": "221-4111111",
		"correo_referente": "direccion@vat.test",
		"referente": str(referente_user.pk),
		"activo": "on",
		"tipo_gestion": "Estatal",
		"clase_institucion": "Formación Profesional",
		"situacion": "Institución de ETP",
		"contactos-TOTAL_FORMS": "1",
		"contactos-INITIAL_FORMS": "0",
		"contactos-MIN_NUM_FORMS": "0",
		"contactos-MAX_NUM_FORMS": "1000",
		"contactos-0-nombre_contacto": "María Gómez",
		"contactos-0-rol_area": "Administración",
		"contactos-0-telefono_contacto": "221-4222222",
		"contactos-0-email_contacto": "maria@vat.test",
		"contactos-0-es_principal": "on",
	}
	payload.update(overrides)
	return payload


@pytest.mark.django_db
def test_centro_create_crea_entidades_relacionadas(vat_admin_client, vat_referente_user, vat_geo_data):
	provincia, municipio, localidad = vat_geo_data
	payload = _build_centro_payload(vat_referente_user, provincia, municipio, localidad, save_continue="1")

	response = vat_admin_client.post(reverse("vat_centro_create"), data=payload)

	centro = Centro.objects.get(codigo="500144900")

	assert response.status_code == 302
	assert response.url == reverse("vat_centro_detail", kwargs={"pk": centro.pk})
	assert AutoridadInstitucional.objects.filter(centro=centro, dni="30111222").exists()
	assert InstitucionContacto.objects.filter(
		centro=centro,
		nombre_contacto="María Gómez",
		es_principal=True,
	).exists()
	assert InstitucionIdentificadorHist.objects.filter(
		centro=centro,
		tipo_identificador="cue",
		valor_identificador="500144900",
	).exists()
	assert InstitucionUbicacion.objects.filter(
		centro=centro,
		rol_ubicacion="sede_principal",
		es_principal=True,
	).exists()


@pytest.mark.django_db
def test_centro_create_requiere_un_contacto_principal(vat_admin_client, vat_referente_user, vat_geo_data):
	provincia, municipio, localidad = vat_geo_data
	payload = _build_centro_payload(
		vat_referente_user,
		provincia,
		municipio,
		localidad,
		**{"contactos-0-es_principal": ""},
	)

	response = vat_admin_client.post(reverse("vat_centro_create"), data=payload)

	assert response.status_code == 200
	assert Centro.objects.filter(codigo="500144900").count() == 0
	assert "Debe existir exactamente un contacto principal." in response.content.decode("utf-8")
