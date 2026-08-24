from decimal import Decimal
from importlib import import_module

import pytest
from django.apps import apps
from django.db import models
from django.template import Context, Engine
from django.utils import timezone

from admisiones.forms.admisiones_forms import InformeTecnicoBaseForm
from admisiones.models.admisiones import (
    Admision,
    InformeTecnico,
    TipoConvenio,
    VariableTemplateInformeTecnico,
)
from admisiones.services.docx_service import AdmisionesContextService
from admisiones.services.informe_tecnico_variables_service import (
    InformeTecnicoVariablesDocumentalesService,
)
from comedores.models import Comedor


def _valor_para_campo(field):
    if field.choices:
        return field.choices[0][0]
    if isinstance(field, models.EmailField):
        return "test@example.com"
    if isinstance(field, (models.CharField, models.TextField)):
        return "test"
    if isinstance(field, models.BooleanField):
        return False
    if isinstance(field, models.DecimalField):
        return Decimal("1.0")
    if isinstance(field, models.DateField):
        return timezone.now().date()
    if isinstance(field, models.IntegerField):
        return 1
    return "test"


def crear_informe(admision, **overrides):
    datos = {}
    for field in InformeTecnico._meta.fields:
        if field.primary_key or field.auto_created or field.has_default():
            continue
        if getattr(field, "auto_now", False) or getattr(field, "auto_now_add", False):
            continue
        if isinstance(field, models.ForeignKey) or field.null:
            continue
        datos[field.name] = _valor_para_campo(field)

    datos.update(
        {
            "admision": admision,
            "tipo": "base",
            "estado": "Validado",
            "estado_formulario": "finalizado",
        }
    )
    datos.update(overrides)
    return InformeTecnico.objects.create(**datos)


@pytest.fixture
def comedor():
    return Comedor.objects.create(nombre="Comedor de prueba")


@pytest.mark.django_db
def test_resuelve_antecedentes_y_totales_desde_admisiones_validas(comedor):
    Admision.objects.create(
        comedor=comedor,
        tipo="incorporacion",
        numero_disposicion="DI-INC-1",
        num_expediente="EXP-INC-1",
    )
    renovacion_anterior = Admision.objects.create(
        comedor=comedor,
        tipo="renovacion",
        numero_disposicion="DI-REN-1",
        numero_convenio="CONV-1",
        num_expediente="EXP-REN-1",
    )
    crear_informe(
        renovacion_anterior,
        aprobadas_desayuno_lunes=10,
        aprobadas_desayuno_martes=2,
        aprobadas_almuerzo_lunes=3,
        aprobadas_merienda_lunes=4,
        aprobadas_cena_lunes=5,
    )
    Admision.objects.create(
        comedor=comedor,
        tipo="renovacion",
        activa=False,
        numero_disposicion="NO-DEBE-USARSE",
        numero_convenio="NO-DEBE-USARSE",
        num_expediente="NO-DEBE-USARSE",
    )
    actual = Admision.objects.create(comedor=comedor, tipo="renovacion")
    informe_actual = crear_informe(
        actual,
        if_it_complementario="IF-2026-123",
        aprobadas_desayuno_lunes=7,
        aprobadas_almuerzo_lunes=8,
        aprobadas_merienda_lunes=9,
        aprobadas_cena_lunes=10,
    )

    valores = InformeTecnicoVariablesDocumentalesService.obtener_valores(informe_actual)

    assert valores["resolucion_o_disposicion_incorporacion"] == "DI-INC-1"
    assert valores["expediente_pago_en_curso"] == "EXP-REN-1"
    assert valores["expediente_ultimo_convenio"] == "EXP-REN-1"
    assert valores["referencia_itcomp_modificacion_prestaciones"] == "IF-2026-123"
    assert valores["total_semanal_ultimo_convenio_desayunos"] == "12"
    assert valores["total_semanal_ultimo_convenio_almuerzos"] == "3"
    assert valores["total_semanal_ultimo_convenio_meriendas"] == "4"
    assert valores["total_semanal_ultimo_convenio_cenas"] == "5"
    assert valores["total_semanal_actual_desayunos"] == "7"
    assert valores["total_semanal_actual_almuerzos"] == "8"
    assert valores["total_semanal_actual_meriendas"] == "9"
    assert valores["total_semanal_actual_cenas"] == "10"
    assert "DI-REN-1" in valores["renovaciones_anteriores_detalladas"]
    assert "CONV-1" in valores["renovaciones_anteriores_detalladas"]
    assert "EXP-REN-1" in valores["renovaciones_anteriores_detalladas"]
    assert "NO-DEBE-USARSE" not in valores["renovaciones_anteriores_detalladas"]


@pytest.mark.django_db
def test_deja_vacias_las_variables_historicas_sin_antecedentes(comedor):
    actual = Admision.objects.create(comedor=comedor, tipo="renovacion")
    informe = crear_informe(actual)

    valores = InformeTecnicoVariablesDocumentalesService.obtener_valores(informe)

    assert valores["resolucion_o_disposicion_incorporacion"] == ""
    assert valores["renovaciones_anteriores_detalladas"] == ""
    assert valores["expediente_pago_en_curso"] == ""
    assert valores["expediente_ultimo_convenio"] == ""
    assert valores["total_semanal_ultimo_convenio_desayunos"] == ""
    assert valores["referencia_itcomp_modificacion_prestaciones"] == ""


@pytest.mark.django_db
def test_renderiza_las_variables_documentales_desde_el_contexto(comedor):
    Admision.objects.create(
        comedor=comedor,
        tipo="incorporacion",
        numero_disposicion="DI-INC-1",
    )
    actual = Admision.objects.create(comedor=comedor, tipo="renovacion")
    informe = crear_informe(actual, if_it_complementario="IF-2026-123")

    contexto = AdmisionesContextService.preparar_contexto_informe_tecnico(informe)
    contenido = (
        Engine(debug=False)
        .from_string(
            "{{ informe.resolucion_o_disposicion_incorporacion }}|"
            "{{ informe.referencia_itcomp_modificacion_prestaciones }}"
        )
        .render(Context(contexto, autoescape=True))
    )

    assert contenido == "DI-INC-1|IF-2026-123"


@pytest.mark.django_db
def test_muestra_if_it_complementario_solo_para_renovacion_con_modificacion(comedor):
    convenio = TipoConvenio.objects.create(nombre="Organización Base")
    admision_con_modificacion = Admision.objects.create(
        comedor=comedor,
        tipo="renovacion",
        tipo_convenio=convenio,
        informe_complementario_modifica_prestaciones="si",
    )
    admision_sin_modificacion = Admision.objects.create(
        comedor=comedor,
        tipo="renovacion",
        tipo_convenio=convenio,
        informe_complementario_modifica_prestaciones="no",
    )

    form_con_modificacion = InformeTecnicoBaseForm(admision=admision_con_modificacion)
    form_sin_modificacion = InformeTecnicoBaseForm(admision=admision_sin_modificacion)

    assert "if_it_complementario" in form_con_modificacion.fields
    assert not form_con_modificacion.fields["if_it_complementario"].required
    assert "if_it_complementario" not in form_sin_modificacion.fields


@pytest.mark.django_db
def test_catalogo_registra_todas_las_variables_documentales():
    migracion = import_module(
        "admisiones.migrations.0079_issue_1213_variables_documentales_renovacion"
    )
    migracion.registrar_variables(apps, None)
    codigos = {
        "informe.resolucion_o_disposicion_incorporacion",
        "informe.renovaciones_anteriores_detalladas",
        "informe.referencia_itcomp_modificacion_prestaciones",
        "informe.expediente_pago_en_curso",
        "informe.expediente_ultimo_convenio",
        *(
            f"informe.total_semanal_ultimo_convenio_{comida}s"
            for comida in ("desayuno", "almuerzo", "merienda", "cena")
        ),
        *(
            f"informe.total_semanal_actual_{comida}s"
            for comida in ("desayuno", "almuerzo", "merienda", "cena")
        ),
    }

    variables = VariableTemplateInformeTecnico.objects.filter(codigo__in=codigos)

    assert set(variables.values_list("codigo", flat=True)) == codigos
    assert not variables.filter(activo=False).exists()
