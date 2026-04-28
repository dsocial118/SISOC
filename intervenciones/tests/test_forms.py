from datetime import datetime

import pytest
from django.utils import timezone

from intervenciones.forms import IntervencionForm
from intervenciones.models.intervenciones import (
    Intervencion,
    SubIntervencion,
    TipoContacto,
    TipoDestinatario,
    TipoIntervencion,
)


def _build_form_data(*, tipo, destinatario, contacto, subintervencion=""):
    return {
        "tipo_intervencion": str(tipo.pk),
        "subintervencion": str(subintervencion) if subintervencion else "",
        "destinatario": str(destinatario.pk),
        "fecha": "2026-04-27 10:00:00",
        "forma_contacto": str(contacto.pk),
        "observaciones": "Seguimiento",
        "tiene_documentacion": "",
    }


@pytest.mark.django_db
def test_intervencion_form_exige_subintervencion_cuando_el_tipo_tiene_opciones():
    tipo = TipoIntervencion.objects.create(nombre="Entrevista", programa="comedores")
    SubIntervencion.objects.create(nombre="Ingreso", tipo_intervencion=tipo)
    destinatario = TipoDestinatario.objects.create(nombre="Titular")
    contacto = TipoContacto.objects.create(nombre="Telefonico")

    form = IntervencionForm(
        data=_build_form_data(
            tipo=tipo,
            destinatario=destinatario,
            contacto=contacto,
        ),
        programa_aliases=("comedores",),
    )

    assert form.is_valid() is False
    assert form.errors["subintervencion"] == ["Debe seleccionar una subintervencion."]


@pytest.mark.django_db
def test_intervencion_form_rechaza_subintervencion_ajena_al_tipo_en_update():
    tipo_valido = TipoIntervencion.objects.create(
        nombre="Entrevista",
        programa="comedores",
    )
    SubIntervencion.objects.create(
        nombre="Ingreso",
        tipo_intervencion=tipo_valido,
    )
    tipo_ajeno = TipoIntervencion.objects.create(nombre="Visita", programa="comedores")
    subtipo_ajeno = SubIntervencion.objects.create(
        nombre="Territorial",
        tipo_intervencion=tipo_ajeno,
    )
    destinatario = TipoDestinatario.objects.create(nombre="Titular")
    contacto = TipoContacto.objects.create(nombre="Telefonico")
    intervencion = Intervencion.objects.create(
        tipo_intervencion=tipo_ajeno,
        subintervencion=subtipo_ajeno,
        destinatario=destinatario,
        forma_contacto=contacto,
        fecha=timezone.make_aware(datetime(2026, 4, 27, 9, 0, 0)),
    )

    form = IntervencionForm(
        data=_build_form_data(
            tipo=tipo_valido,
            subintervencion=subtipo_ajeno.pk,
            destinatario=destinatario,
            contacto=contacto,
        ),
        instance=intervencion,
        programa_aliases=("comedores",),
    )

    assert form.is_valid() is False
    assert form.errors["subintervencion"] == [
        "La subintervencion seleccionada no corresponde al tipo de intervencion."
    ]
