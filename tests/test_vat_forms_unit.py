"""Tests unitarios para VAT.forms."""

from types import SimpleNamespace

import pytest

from VAT import forms as module


def test_get_including_deleted_manager_prefiere_all_objects():
    all_objects = SimpleNamespace(name="all_objects")
    objects = SimpleNamespace(name="objects")
    model_class = SimpleNamespace(all_objects=all_objects, objects=objects)

    assert module._get_including_deleted_manager(model_class) is all_objects


def test_get_including_deleted_manager_usa_objects_como_fallback():
    objects = SimpleNamespace(name="objects")
    model_class = SimpleNamespace(objects=objects)

    assert module._get_including_deleted_manager(model_class) is objects


def test_select2_attrs_agrega_clase_placeholder_y_width():
    attrs = module._select2_attrs(
        base_class="form-select",
        placeholder="Seleccionar...",
        allow_clear=True,
        **{"data-minimum-input-length": 2},
    )

    assert set(attrs["class"].split()) == {"form-select", "select2"}
    assert attrs["data-placeholder"] == "Seleccionar..."
    assert attrs["data-allow-clear"] == "true"
    assert attrs["data-width"] == "100%"
    assert attrs["data-minimum-input-length"] == 2


@pytest.mark.parametrize(
    ("form_class", "field_name"),
    [
        (module.CentroAltaForm, "provincia"),
        (module.CentroAltaForm, "municipio"),
        (module.CentroAltaForm, "localidad"),
        (module.SubsectorForm, "sector"),
        (module.TituloReferenciaForm, "plan_estudio"),
        (module.PlanVersionCurricularForm, "sector"),
        (module.PlanVersionCurricularForm, "subsector"),
        (module.PlanVersionCurricularForm, "modalidad_cursada"),
        (module.InscripcionOfertaForm, "oferta"),
        (module.InscripcionOfertaForm, "ciudadano"),
        (module.InstitucionUbicacionForm, "centro"),
        (module.InstitucionUbicacionForm, "localidad"),
        (module.OfertaInstitucionalForm, "centro"),
        (module.OfertaInstitucionalForm, "titulo_referencia"),
        (module.OfertaInstitucionalForm, "programa"),
        (module.ComisionForm, "oferta"),
        (module.ComisionForm, "ubicacion"),
        (module.ComisionHorarioForm, "comision"),
        (module.ComisionCursoHorarioForm, "comision_curso"),
        (module.InscripcionForm, "ciudadano"),
        (module.InscripcionForm, "comision"),
        (module.EvaluacionForm, "comision"),
        (module.ResultadoEvaluacionForm, "evaluacion"),
        (module.ResultadoEvaluacionForm, "inscripcion"),
        (module.VoucherForm, "ciudadano"),
        (module.VoucherForm, "programa"),
    ],
)
def test_vat_forms_relacionales_relevantes_usan_select2(form_class, field_name):
    field = form_class.base_fields[field_name]

    assert "select2" in field.widget.attrs["class"].split()
    assert field.widget.attrs["data-width"] == "100%"
