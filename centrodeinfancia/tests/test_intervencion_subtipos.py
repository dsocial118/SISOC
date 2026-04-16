import json

import pytest
from django.test import Client
from django.urls import reverse

from centrodeinfancia.forms import IntervencionCentroInfanciaForm
from intervenciones.models.intervenciones import SubIntervencion, TipoIntervencion


@pytest.mark.django_db
def test_intervencion_cdi_form_inicia_sin_subtipos_globales():
    tipo = TipoIntervencion.objects.create(nombre="Seguimiento", programa="cdi")
    SubIntervencion.objects.create(nombre="Visible", tipo_intervencion=tipo)

    form = IntervencionCentroInfanciaForm()

    assert list(form.fields["subintervencion"].queryset) == []


@pytest.mark.django_db
def test_intervencion_cdi_form_filtra_subtipos_por_tipo_y_excluye_vacios():
    tipo_cdi = TipoIntervencion.objects.create(nombre="Seguimiento", programa="cdi")
    otro_tipo = TipoIntervencion.objects.create(nombre="Otro", programa="cdi")
    subtipo_valido = SubIntervencion.objects.create(
        nombre="Visita",
        tipo_intervencion=tipo_cdi,
    )
    SubIntervencion.objects.create(nombre="", tipo_intervencion=tipo_cdi)
    SubIntervencion.objects.create(nombre="No corresponde", tipo_intervencion=otro_tipo)

    form = IntervencionCentroInfanciaForm(
        data={"tipo_intervencion": str(tipo_cdi.id), "subintervencion": ""}
    )

    assert list(form.fields["subintervencion"].queryset) == [subtipo_valido]


@pytest.mark.django_db
def test_ajax_subtipos_filtra_por_tipo_y_excluye_nombres_vacios(django_user_model):
    user = django_user_model.objects.create_user(
        username="tester-subtipos",
        password="secret123",
    )
    client = Client()
    client.force_login(user)

    tipo_cdi = TipoIntervencion.objects.create(nombre="Seguimiento", programa="cdi")
    otro_tipo = TipoIntervencion.objects.create(nombre="Otro", programa="cdi")
    subtipo_valido = SubIntervencion.objects.create(
        nombre="Visita",
        tipo_intervencion=tipo_cdi,
    )
    SubIntervencion.objects.create(nombre="", tipo_intervencion=tipo_cdi)
    SubIntervencion.objects.create(nombre="No corresponde", tipo_intervencion=otro_tipo)

    response = client.get(
        reverse("ajax_load_subestadosintervenciones"),
        {"id": tipo_cdi.id},
    )

    assert response.status_code == 200
    assert json.loads(response.content) == [{"id": subtipo_valido.id, "text": "Visita"}]
