from datetime import date
from pathlib import Path

import pytest
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import RequestFactory
from django.urls import reverse

from ciudadanos.models import Ciudadano
from centrodeinfancia.forms import NominaCentroInfanciaCreateForm
from centrodeinfancia.models import CentroDeInfancia, NominaCentroInfancia
from centrodeinfancia.views import NominaCentroInfanciaCreateView
from core.models import Localidad, Municipio, Provincia, Sexo


@pytest.mark.django_db(transaction=True)
def test_crear_nomina_con_bloqueo_evitar_duplicados():
    provincia = Provincia.objects.create(nombre="Rio Negro")
    centro = CentroDeInfancia.objects.create(nombre="CDI RN", provincia=provincia)
    ciudadano = Ciudadano.objects.create(
        apellido="Lopez",
        nombre="Ana",
        fecha_nacimiento=date(2012, 5, 10),
        documento=33333333,
    )

    with transaction.atomic():
        creado_1 = NominaCentroInfanciaCreateView._crear_nomina_con_bloqueo(
            centro=centro,
            ciudadano=ciudadano,
            cleaned_data={
                "estado": NominaCentroInfancia.ESTADO_ACTIVO,
                "observaciones": "Alta inicial",
            },
        )

    with transaction.atomic():
        creado_2 = NominaCentroInfanciaCreateView._crear_nomina_con_bloqueo(
            centro=centro,
            ciudadano=ciudadano,
            cleaned_data={
                "estado": NominaCentroInfancia.ESTADO_ACTIVO,
                "observaciones": "Intento duplicado",
            },
        )

    assert creado_1 is True
    assert creado_2 is False
    assert (
        NominaCentroInfancia.objects.filter(
            centro=centro,
            ciudadano=ciudadano,
            deleted_at__isnull=True,
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_nomina_requiere_detalle_pueblo_originario_si_responde_si():
    nomina = NominaCentroInfancia(
        pertenece_pueblo_originario=NominaCentroInfancia.RespuestaSiNoNsNc.SI,
        tiene_discapacidad=NominaCentroInfancia.RespuestaSiNoNsNc.NO,
    )

    with pytest.raises(ValidationError) as exc_info:
        nomina.clean()

    assert "pueblo_originario_cual" in exc_info.value.message_dict


@pytest.mark.django_db
def test_form_nomina_calcula_edad_y_habilita_geografia():
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    sexo = Sexo.objects.create(sexo="Femenino")

    form = NominaCentroInfanciaCreateForm(
        data={
            "estado": NominaCentroInfancia.ESTADO_ACTIVO,
            "dni": 30111222,
            "apellido": "Lopez",
            "nombre": "Ana",
            "fecha_nacimiento": "2018-05-10",
            "sexo": sexo.sexo,
            "provincia_domicilio": provincia.id,
        }
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["edad_calculada"] is not None
    municipio_ids = set(
        form.fields["municipio_domicilio"].queryset.values_list("id", flat=True)
    )
    assert municipio_ids == set()


@pytest.mark.django_db
def test_form_nomina_resuelve_geografia_inicial_desde_texto():
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Tolosa", municipio=municipio)
    sexo = Sexo.objects.create(sexo="Femenino")

    form = NominaCentroInfanciaCreateForm(
        initial={
            "estado": NominaCentroInfancia.ESTADO_ACTIVO,
            "dni": 30111222,
            "apellido": "Lopez",
            "nombre": "Ana",
            "fecha_nacimiento": date(2018, 5, 10),
            "sexo": sexo.sexo,
            "provincia_domicilio": "Buenos Aires",
            "municipio_domicilio": "La Plata",
            "localidad_domicilio": "Tolosa",
        }
    )

    assert form.fields["provincia_domicilio"].initial == provincia
    assert form.fields["municipio_domicilio"].initial == municipio
    assert form.fields["localidad_domicilio"].initial == localidad


@pytest.mark.django_db
def test_create_view_precarga_fecha_renaper_desde_contrato_servicio(mocker):
    user = User.objects.create_superuser(
        username="super-cdi-renaper",
        email="super-cdi-renaper@example.com",
        password="test1234",
    )
    centro = CentroDeInfancia.objects.create(nombre="CDI RENAPER")
    request = RequestFactory().get(
        reverse("centrodeinfancia_nomina_crear", kwargs={"pk": centro.pk}),
        {"query": "30111222"},
    )
    request.user = user
    mock_obtener = mocker.patch(
        "centrodeinfancia.views.ComedorService.obtener_datos_ciudadano_desde_renaper",
        return_value={
            "success": True,
            "data": {
                "documento": 30111222,
                "apellido": "Lopez",
                "nombre": "Ana",
                "sexo": "Femenino",
            },
            "datos_api": {
                "fechaNacimiento": "2018-05-10",
            },
        },
    )

    view = NominaCentroInfanciaCreateView()
    view.setup(request, pk=centro.pk)
    view.object = None
    context = view.get_context_data()
    initial = context["form"].initial

    assert initial["dni"] == 30111222
    assert initial["apellido"] == "Lopez"
    assert initial["nombre"] == "Ana"
    assert initial["fecha_nacimiento"] == date(2018, 5, 10)
    assert context["renaper_precarga"] is True
    mock_obtener.assert_called_once_with("30111222")


@pytest.mark.django_db
def test_create_view_crea_ficha_cdi_para_ciudadano_existente(client):
    user = User.objects.create_superuser(
        username="super-cdi-nomina",
        email="super-cdi-nomina@example.com",
        password="test1234",
    )
    client.force_login(user)
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    sexo = Sexo.objects.create(sexo="Femenino")
    centro = CentroDeInfancia.objects.create(nombre="CDI Norte", provincia=provincia)
    ciudadano = Ciudadano.objects.create(
        apellido="Perez",
        nombre="Nina",
        fecha_nacimiento=date(2020, 4, 2),
        tipo_documento=Ciudadano.DOCUMENTO_DNI,
        documento=40111222,
        sexo=sexo,
    )

    response = client.post(
        reverse("centrodeinfancia_nomina_crear", kwargs={"pk": centro.pk}),
        data={
            "ciudadano_id": ciudadano.id,
            "estado": NominaCentroInfancia.ESTADO_ACTIVO,
            "dni": ciudadano.documento,
            "apellido": ciudadano.apellido,
            "nombre": ciudadano.nombre,
            "fecha_nacimiento": "2020-04-02",
            "sexo": sexo.sexo,
            "sala": "Sala Roja",
            "posee_cud": "false",
            "posee_obra_social": "true",
        },
    )

    assert response.status_code == 302
    nomina = NominaCentroInfancia.objects.get(centro=centro, ciudadano=ciudadano)
    assert nomina.sala == "Sala Roja"
    assert nomina.posee_cud is False
    assert nomina.posee_obra_social is True


def test_nomina_crear_template_conserva_ajax_nativo_ubicacion():
    template_path = (
        Path(settings.BASE_DIR)
        / "centrodeinfancia/templates/centrodeinfancia/nomina_form.html"
    )
    content = template_path.read_text(encoding="utf-8")

    assert "ajaxLoadMunicipiosUrl" in content
    assert "ajaxLoadLocalidadesUrl" in content
    assert "id_provincia_domicilio" in content
    assert "id_municipio_domicilio" in content
    assert "id_localidad_domicilio" in content
    assert "fetch(url" in content
