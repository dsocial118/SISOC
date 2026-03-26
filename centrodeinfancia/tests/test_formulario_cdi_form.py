import pytest
from django.contrib.auth.models import User

from centrodeinfancia.forms import FormularioCDIForm
from centrodeinfancia.models import CentroDeInfancia
from core.models import Localidad, Municipio, Provincia


@pytest.mark.django_db
def test_formulario_cdi_requiere_texto_para_jornada_otra():
    centro = CentroDeInfancia.objects.create(nombre="CDI Norte")
    form = FormularioCDIForm(
        data={
            "cdi_name": centro.nombre,
            "cdi_code": centro.cdi_code,
            "workday_type": "other",
        }
    )

    assert not form.is_valid()
    assert "workday_type_other" in form.errors


@pytest.mark.django_db
def test_formulario_cdi_no_permite_meals_ninguna_con_otras():
    centro = CentroDeInfancia.objects.create(nombre="CDI Sur")
    form = FormularioCDIForm(
        data={
            "cdi_name": centro.nombre,
            "cdi_code": centro.cdi_code,
            "meals_provided": ["ninguna", "desayuno"],
        }
    )

    assert not form.is_valid()
    assert "meals_provided" in form.errors


@pytest.mark.django_db
def test_formulario_cdi_form_acepta_payload_minimo():
    user = User.objects.create_user(username="formulario-minimo", password="test1234")
    centro = CentroDeInfancia.objects.create(nombre="CDI Este")
    form = FormularioCDIForm(
        data={
            "survey_date": "2026-03-13",
            "respondent_full_name": "Ana Perez",
            "respondent_role": "Coordinacion",
            "respondent_email": "ana@example.com",
            "cdi_name": centro.nombre,
            "cdi_code": centro.cdi_code,
            "source_form_version": 1,
        }
    )

    assert form.is_valid(), form.errors
    instance = form.save(commit=False)
    instance.centro = centro
    instance.created_by = user
    instance.save()

    assert instance.pk is not None


@pytest.mark.django_db
def test_formulario_cdi_filtra_municipio_y_localidad_por_ubicacion_seleccionada():
    provincia_ba = Provincia.objects.create(nombre="Buenos Aires")
    provincia_sf = Provincia.objects.create(nombre="Santa Fe")
    municipio_ba = Municipio.objects.create(nombre="La Plata", provincia=provincia_ba)
    Municipio.objects.create(nombre="Rosario", provincia=provincia_sf)
    localidad_ba = Localidad.objects.create(nombre="Tolosa", municipio=municipio_ba)
    Localidad.objects.create(
        nombre="Fisherton",
        municipio=Municipio.objects.get(nombre="Rosario"),
    )

    form = FormularioCDIForm(
        data={
            "cdi_province": provincia_ba.pk,
            "cdi_municipality": municipio_ba.pk,
            "cdi_locality": localidad_ba.pk,
        }
    )

    municipio_ids = set(
        form.fields["cdi_municipality"].queryset.values_list("id", flat=True)
    )
    localidad_ids = set(
        form.fields["cdi_locality"].queryset.values_list("id", flat=True)
    )

    assert municipio_ids == {municipio_ba.id}
    assert localidad_ids == {localidad_ba.id}


@pytest.mark.django_db
def test_formulario_cdi_labels_custom_quedan_en_espanol():
    form = FormularioCDIForm()

    assert form.fields["operation_months"].label == "Meses de funcionamiento del CDI"
    assert form.fields["operation_days"].label == "Días de funcionamiento del CDI"
    assert (
        form.fields["has_fire_extinguishers_current"].label
        == "Existencia de extintores"
    )
    assert form.fields["has_admission_prioritization_tool"].label == (
        "Existe instrumento de priorización de ingreso de los niños/as"
    )


@pytest.mark.django_db
def test_formulario_cdi_limpia_valores_de_campos_ocultos_por_skip_logic():
    centro = CentroDeInfancia.objects.create(nombre="CDI Ocultos")
    form = FormularioCDIForm(
        data={
            "cdi_name": centro.nombre,
            "cdi_code": centro.cdi_code,
            "has_kitchen_space": "no",
            "cooking_fuel": "gas_red",
            "has_outdoor_space": "no",
            "has_outdoor_playground": "si",
            "meals_provided": ["ninguna"],
            "menu_preparation_quality": "sin_nutricionista_ultraprocesados",
            "source_form_version": 1,
        }
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["cooking_fuel"] == ""
    assert form.cleaned_data["has_outdoor_playground"] == ""
    assert form.cleaned_data["menu_preparation_quality"] == ""


@pytest.mark.django_db
def test_formulario_cdi_limpia_seguridad_electrica_si_no_tiene_electricidad():
    centro = CentroDeInfancia.objects.create(nombre="CDI Sin Electricidad")
    form = FormularioCDIForm(
        data={
            "cdi_name": centro.nombre,
            "cdi_code": centro.cdi_code,
            "electricity_access": "sin_electricidad",
            "electrical_safety": "cumple_y_revision_anual",
            "source_form_version": 1,
        }
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["electrical_safety"] == ""


@pytest.mark.django_db
def test_formulario_cdi_aplica_textos_actualizados_en_labels_y_opciones():
    form = FormularioCDIForm()

    assert form.fields["survey_date"].label == "Fecha de Relevamiento"
    assert (
        form.fields["internet_access_quality_staff"].label
        == "Acceso a internet: ¿El CDI tiene acceso a internet y es compartido por el personal?"
    )
    assert (
        dict(form.fields["water_access"].choices)["caneria_dentro_cdi"]
        == "Por cañería dentro del CDI"
    )
