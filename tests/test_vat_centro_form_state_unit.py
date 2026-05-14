from pathlib import Path

import pytest
from django.contrib.auth.models import Group, User

from VAT.forms import CentroAltaForm
from VAT.models import Centro
from core.models import Localidad, Municipio, Provincia


def _build_centro_form_data(referente, provincia, municipio, localidad, **overrides):
    data = {
        "nombre": "Centro de Formacion 401",
        "codigo": "500144900",
        "provincia": str(provincia.pk),
        "municipio": str(municipio.pk),
        "localidad": str(localidad.pk),
        "calle": "7",
        "numero": "1234",
        "domicilio_actividad": "Calle 7 N 1234",
        "codigo_postal": "1900",
        "lote": "12",
        "manzana": "B",
        "entre_calles": "45 y 46",
        "telefono": "221-4000000",
        "celular": "221-5000000",
        "correo": "institucion@vat.test",
        "sitio_web": "https://vat.test",
        "nombre_referente": "Ana",
        "apellido_referente": "Perez",
        "autoridad_dni": "30111222",
        "telefono_referente": "221-4111111",
        "correo_referente": "direccion@vat.test",
        "referente": str(referente.pk),
        "tipo_gestion": "Estatal",
        "clase_institucion": "Formación Profesional",
        "situacion": "Institución de ETP",
    }
    data.update(overrides)
    return data


@pytest.fixture
def vat_centro_form_context(db):
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    municipio = Municipio.objects.create(nombre="La Plata", provincia=provincia)
    localidad = Localidad.objects.create(nombre="Tolosa", municipio=municipio)
    group, _ = Group.objects.get_or_create(name="CFP")
    referente = User.objects.create_user(username="referente-form", password="test1234")
    referente.groups.add(group)
    return provincia, municipio, localidad, referente


def _build_centro_instance(provincia, municipio, localidad, referente, activo=True):
    return Centro.objects.create(
        nombre="Centro de Formacion 401",
        codigo="500144900",
        provincia=provincia,
        municipio=municipio,
        localidad=localidad,
        calle="7",
        numero=1234,
        domicilio_actividad="Calle 7 N 1234",
        codigo_postal="1900",
        lote="12",
        manzana="B",
        entre_calles="45 y 46",
        telefono="221-4000000",
        celular="221-5000000",
        correo="institucion@vat.test",
        sitio_web="https://vat.test",
        nombre_referente="Ana",
        apellido_referente="Perez",
        telefono_referente="221-4111111",
        correo_referente="direccion@vat.test",
        referente=referente,
        tipo_gestion="Estatal",
        clase_institucion="Formación Profesional",
        situacion="Institución de ETP",
        activo=activo,
    )


@pytest.mark.django_db
def test_centro_alta_form_preserva_activo_si_no_envia_switch(vat_centro_form_context):
    provincia, municipio, localidad, referente = vat_centro_form_context
    centro = _build_centro_instance(
        provincia, municipio, localidad, referente, activo=True
    )
    form = CentroAltaForm(
        data=_build_centro_form_data(referente, provincia, municipio, localidad),
        instance=centro,
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["activo"] is True


@pytest.mark.django_db
def test_centro_alta_form_permite_desactivar_si_envia_switch(vat_centro_form_context):
    provincia, municipio, localidad, referente = vat_centro_form_context
    centro = _build_centro_instance(
        provincia, municipio, localidad, referente, activo=True
    )
    form = CentroAltaForm(
        data=_build_centro_form_data(
            referente,
            provincia,
            municipio,
            localidad,
            activo_present="1",
        ),
        instance=centro,
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["activo"] is False


@pytest.mark.django_db
def test_centro_alta_form_permite_reactivar_si_envia_switch(vat_centro_form_context):
    provincia, municipio, localidad, referente = vat_centro_form_context
    centro = _build_centro_instance(
        provincia,
        municipio,
        localidad,
        referente,
        activo=False,
    )
    form = CentroAltaForm(
        data=_build_centro_form_data(
            referente,
            provincia,
            municipio,
            localidad,
            activo_present="1",
            activo="on",
        ),
        instance=centro,
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["activo"] is True


def test_template_centro_create_form_incluye_switch_activo():
    template_path = (
        Path(__file__).resolve().parents[1]
        / "VAT"
        / "templates"
        / "vat"
        / "centros"
        / "centro_create_form.html"
    )
    content = template_path.read_text(encoding="utf-8")

    assert 'name="activo_present"' in content
    assert "4. Estado de la sede" in content
