"""Campos de "Referencia a la Incorporación" en el borrador del informe.

La sección solo aplica a renovaciones: en una incorporación el formulario
descarta esos campos, así que no se renderizan ni se exigen. En renovación se
guardan con el borrador y recién al finalizar son obligatorios.
"""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory

from admisiones.forms.admisiones_forms import (
    CaratularForm,
    InformeTecnicoBaseForm,
)
from admisiones.models.admisiones import Admision, InformeTecnico, TipoConvenio
from admisiones.views.web_views import CARATULA_FORM_PREFIX
from comedores.models import Comedor

pytestmark = pytest.mark.django_db

CAMPOS_REFERENCIA = (
    "expediente_incorporacion",
    "convenio_incorporacion",
    "presentacion_avales",
    "informe_tecnico_complementario_modificacion_prestaciones",
    "if_it_complementario",
)

PLANTILLAS = (
    "admisiones/informe_tecnico_form.html",
    "admisiones/admisiones_tecnicos_form.html",
)


def _crear_admision(tipo="renovacion"):
    comedor = Comedor.objects.create(nombre=f"Comedor {Comedor.objects.count() + 1}")
    tipo_convenio = TipoConvenio.objects.create(
        nombre=f"Convenio {TipoConvenio.objects.count() + 1}"
    )
    return Admision.objects.create(
        comedor=comedor,
        tipo_convenio=tipo_convenio,
        tipo=tipo,
        tipo_renovacion="primera",
        estado_financiamiento="finalizado",
        informe_complementario_modifica_prestaciones="si",
    )


def _render(plantilla, admision):
    request = RequestFactory().get("/x")
    request.csp_nonce = "n"
    request.user = AnonymousUser()
    form = InformeTecnicoBaseForm(instance=None, admision=admision)
    return render_to_string(
        plantilla,
        {
            "request": request,
            "admision": admision,
            "comedor": admision.comedor,
            "tipo": "base",
            "informe_tipo": "base",
            "form": form,
            "informe_form": form,
            "botones_disponibles": [],
            "documentos": [],
            "documentos_personalizados": [],
            "stats": {},
            "caratular_form": CaratularForm(instance=admision),
            "caratular_form_informe": CaratularForm(
                instance=admision, prefix=CARATULA_FORM_PREFIX, borrador=True
            ),
        },
        request=request,
    )


@pytest.mark.parametrize("plantilla", PLANTILLAS)
@pytest.mark.parametrize("campo", CAMPOS_REFERENCIA)
def test_renovacion_renderiza_todos_los_campos_de_referencia(plantilla, campo):
    """Regresión: `if_it_complementario` no se renderizaba en ninguna pantalla."""
    html = _render(plantilla, _crear_admision("renovacion"))

    assert "Referencia a la Incorporaci" in html
    assert f'name="{campo}"' in html, f"{campo} no llegó a la pantalla"


@pytest.mark.parametrize("plantilla", PLANTILLAS)
def test_incorporacion_no_muestra_la_seccion(plantilla):
    html = _render(plantilla, _crear_admision("incorporacion"))

    assert "Referencia a la Incorporaci" not in html
    for campo in CAMPOS_REFERENCIA:
        assert f'name="{campo}"' not in html


def test_todo_campo_exigido_al_finalizar_esta_en_pantalla():
    """Ningún campo obligatorio puede quedar fuera del formulario.

    Es lo que hacía imposible finalizar: `if_it_complementario` se volvía
    obligatorio pero no se renderizaba, así que el POST nunca lo traía.
    """
    admision = _crear_admision("renovacion")
    form = InformeTecnicoBaseForm(instance=None, admision=admision, require_full=True)
    obligatorios = {nombre for nombre, campo in form.fields.items() if campo.required}
    assert "if_it_complementario" in obligatorios, "cambió la condición del campo"

    html = _render("admisiones/admisiones_tecnicos_form.html", admision)
    faltantes = [
        nombre
        for nombre in obligatorios
        if f'name="{nombre}"' not in html and f'id="id_{nombre}"' not in html
    ]
    assert not faltantes, f"campos obligatorios sin renderizar: {faltantes}"


@pytest.mark.parametrize("campo", CAMPOS_REFERENCIA)
def test_en_incorporacion_el_campo_no_existe_ni_se_exige(campo):
    admision = _crear_admision("incorporacion")

    form = InformeTecnicoBaseForm(instance=None, admision=admision, require_full=True)

    assert campo not in form.fields


def test_el_borrador_guarda_los_campos_sin_exigirlos():
    admision = _crear_admision("renovacion")
    informe = InformeTecnico.objects.create(
        admision=admision, tipo="base", estado="Iniciado", estado_formulario="borrador"
    )

    form = InformeTecnicoBaseForm(
        data={"if_it_complementario": "IF-2026-1-APN-DPS#MCH"},
        instance=informe,
        admision=admision,
        require_full=False,
    )

    assert form.is_valid(), form.errors
    form.save()
    informe.refresh_from_db()
    assert informe.if_it_complementario == "IF-2026-1-APN-DPS#MCH"


def test_al_finalizar_se_exigen_los_campos_de_referencia():
    admision = _crear_admision("renovacion")
    informe = InformeTecnico.objects.create(
        admision=admision, tipo="base", estado="Iniciado", estado_formulario="borrador"
    )

    form = InformeTecnicoBaseForm(
        data={}, instance=informe, admision=admision, require_full=True
    )

    assert not form.is_valid()
    for campo in CAMPOS_REFERENCIA:
        assert campo in form.errors, f"{campo} debería ser obligatorio al finalizar"
