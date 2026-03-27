import pytest

from centrodeinfancia.forms import IntervencionCentroInfanciaForm
from intervenciones.models.intervenciones import (
    SubIntervencion,
    TipoContacto,
    TipoDestinatario,
    TipoIntervencion,
)


def _base_form_data(tipo_id, subtipo_id=""):
    destinatario = TipoDestinatario.objects.create(nombre="Familiar")
    contacto = TipoContacto.objects.create(nombre="Presencial")
    return {
        "tipo_intervencion": str(tipo_id),
        "subintervencion": str(subtipo_id) if subtipo_id else "",
        "destinatario": str(destinatario.id),
        "fecha": "2024-01-10",
        "forma_contacto": str(contacto.id),
        "observaciones": "Prueba",
    }


def _base_form_data_sin_destinatario(tipo_id, subtipo_id=""):
    contacto = TipoContacto.objects.create(nombre="Presencial")
    return {
        "tipo_intervencion": str(tipo_id),
        "subintervencion": str(subtipo_id) if subtipo_id else "",
        "fecha": "2024-01-10",
        "forma_contacto": str(contacto.id),
        "observaciones": "Prueba",
    }


@pytest.mark.django_db
def test_cdi_intervencion_requiere_subintervencion_si_el_tipo_tiene_subtipos():
    tipo = TipoIntervencion.objects.create(nombre="Seguimiento", programa="cdi")
    SubIntervencion.objects.create(nombre="Presencial", tipo_intervencion=tipo)

    form = IntervencionCentroInfanciaForm(data=_base_form_data(tipo.id))

    assert not form.is_valid()
    assert "subintervencion" in form.errors
    assert "Debe seleccionar una subintervención." in form.errors["subintervencion"][0]


@pytest.mark.django_db
def test_cdi_intervencion_rechaza_subintervencion_de_otro_tipo():
    tipo_1 = TipoIntervencion.objects.create(nombre="Tipo 1", programa="cdi")
    tipo_2 = TipoIntervencion.objects.create(nombre="Tipo 2", programa="cdi")
    subtipo_otro = SubIntervencion.objects.create(
        nombre="Subtipo 2",
        tipo_intervencion=tipo_2,
    )

    form = IntervencionCentroInfanciaForm(
        data=_base_form_data(tipo_1.id, subtipo_id=subtipo_otro.id)
    )

    assert not form.is_valid()
    assert "subintervencion" in form.errors
    assert "no corresponde al tipo de intervención" in form.errors["subintervencion"][0]


@pytest.mark.django_db
def test_cdi_intervencion_acepta_tipo_sin_subintervenciones():
    tipo = TipoIntervencion.objects.create(nombre="Entrevista", programa="cdi")

    form = IntervencionCentroInfanciaForm(data=_base_form_data(tipo.id))

    assert form.is_valid(), form.errors
    assert form.cleaned_data["subintervencion"] is None


@pytest.mark.django_db
def test_cdi_intervencion_destinatario_fijo_centro():
    tipo = TipoIntervencion.objects.create(nombre="Seguimiento", programa="cdi")
    destinatario_centro = TipoDestinatario.objects.create(nombre="Centro")

    form = IntervencionCentroInfanciaForm(
        data=_base_form_data_sin_destinatario(tipo.id),
        destinatario_fijo_nombre="Centro",
        hide_destinatario=True,
    )

    assert form.is_valid(), form.errors
    assert form.cleaned_data["destinatario"] == destinatario_centro
