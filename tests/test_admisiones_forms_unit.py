"""Unit tests for helpers and forms in admisiones forms module."""

from decimal import Decimal
from types import SimpleNamespace

import pytest

from admisiones.forms.admisiones_forms import (
    IntervencionJuridicosForm,
    InformeTecnicoEstadoForm,
    LegalesNumIFForm,
    MontoDecimalField,
    _armar_domicilio,
    _if_relevamiento_a_pac,
    _permite_no_corresponde_fecha_vencimiento,
    _ultimo_numero_gde,
)
from admisiones.models.admisiones import Admision


def test_armar_domicilio_con_valores_completos():
    """Concatena calle y número cuando ambos están presentes."""
    assert _armar_domicilio("Av Siempre Viva", "742") == "Av Siempre Viva 742"


def test_armar_domicilio_usa_default_si_vacio():
    """Retorna el valor por defecto cuando no hay datos útiles."""
    assert _armar_domicilio(" ", None) == "Sin definir"
    assert _armar_domicilio(None, None, default="N/D") == "N/D"


@pytest.mark.parametrize(
    "tipo,nombre_convenio,esperado",
    [
        ("incorporacion", "Personería Jurídica Eclesiástica", True),
        ("renovacion", "Personeria Juridica Eclesiastica", True),
        ("incorporacion", "Convenio General", False),
        ("baja", "Personería Jurídica Eclesiástica", False),
    ],
)
def test_permite_no_corresponde_fecha_vencimiento(tipo, nombre_convenio, esperado):
    """Valida regla por tipo de admisión y normalización del nombre de convenio."""
    admision = SimpleNamespace(
        tipo=tipo,
        tipo_convenio=SimpleNamespace(nombre=nombre_convenio),
    )
    assert _permite_no_corresponde_fecha_vencimiento(admision) is esperado


def test_monto_decimal_field_parsea_coma_y_miles():
    """Normaliza formatos con coma decimal y separadores de miles."""
    field = MontoDecimalField(required=False)
    assert field.to_python("1.234,56") == Decimal("1234.56")
    assert field.to_python("1.234") == Decimal("1234")
    assert field.to_python("1234.5") == Decimal("1234.5")


def test_ultimo_numero_gde_arma_query_y_devuelve_first(mocker):
    """Construye el queryset esperado y retorna el primer número GDE."""
    first_mock = mocker.Mock(return_value="GDE-123")
    values_list_mock = mocker.Mock(return_value=SimpleNamespace(first=first_mock))
    order_by_mock = mocker.Mock(return_value=SimpleNamespace(values_list=values_list_mock))
    exclude_second = SimpleNamespace(order_by=order_by_mock)
    exclude_first = SimpleNamespace(exclude=mocker.Mock(return_value=exclude_second))
    filter_mock = mocker.patch(
        "admisiones.forms.admisiones_forms.ArchivoAdmision.objects.filter",
        return_value=SimpleNamespace(exclude=mocker.Mock(return_value=exclude_first)),
    )

    admision = object()
    result = _ultimo_numero_gde(admision, "Relevamiento Programa PAC")

    assert result == "GDE-123"
    filter_mock.assert_called_once_with(
        admision=admision,
        documentacion__nombre="Relevamiento Programa PAC",
    )


def test_if_relevamiento_a_pac_setea_iniciales(mocker):
    """Propaga el último GDE a ambos campos de relevamiento cuando existe."""
    mocker.patch(
        "admisiones.forms.admisiones_forms._ultimo_numero_gde",
        return_value="GDE-XYZ",
    )
    fields = {
        "if_relevamiento": SimpleNamespace(initial=None),
        "IF_relevamiento_territorial": SimpleNamespace(initial=None),
    }

    out = _if_relevamiento_a_pac(fields, admision=object())

    assert out["if_relevamiento"].initial == "GDE-XYZ"
    assert out["IF_relevamiento_territorial"].initial == "GDE-XYZ"


def test_if_relevamiento_a_pac_no_modifica_sin_admision(mocker):
    """No modifica campos cuando no hay admisión válida."""
    spy = mocker.patch("admisiones.forms.admisiones_forms._ultimo_numero_gde")
    fields = {"if_relevamiento": SimpleNamespace(initial="ORIGINAL")}

    out = _if_relevamiento_a_pac(fields, admision=None)

    assert out["if_relevamiento"].initial == "ORIGINAL"
    spy.assert_not_called()


def test_informe_tecnico_estado_form_requiere_campos_para_subsanar():
    """Exige campos a subsanar cuando el estado es A subsanar."""
    form = InformeTecnicoEstadoForm(data={"estado": "A subsanar", "observacion": "x"})

    assert not form.is_valid()
    assert "Debe marcar al menos un campo" in str(form.errors)


def test_informe_tecnico_estado_form_valido_en_validado_sin_campos():
    """Permite estado validado sin selección de campos."""
    form = InformeTecnicoEstadoForm(data={"estado": "Validado"})
    assert form.is_valid()


@pytest.mark.django_db
def test_legales_num_if_form_precarga_y_readonly():
    """Precarga legales_num_if y bloquea edición cuando hay expediente."""
    admision = Admision(num_expediente="EX-1", legales_num_if="")

    form = LegalesNumIFForm(instance=admision)

    assert form.initial["legales_num_if"] == "EX-1"
    assert form.fields["legales_num_if"].widget.attrs["readonly"] is True
    assert "Informe Técnico" in form.fields["legales_num_if"].help_text


@pytest.mark.django_db
def test_intervencion_juridicos_form_exige_motivo_si_rechazado():
    """Rechazado sin motivo debe disparar error de validación."""
    form = IntervencionJuridicosForm(
        data={
            "intervencion_juridicos": "rechazado",
            "rechazo_juridicos_motivo": "",
            "dictamen_motivo": "",
        }
    )

    assert not form.is_valid()
    assert "rechazo_juridicos_motivo" in form.errors


@pytest.mark.django_db
def test_intervencion_juridicos_form_exige_dictamen_detalle():
    """Si motivo es dictamen, también exige detalle de dictamen."""
    form = IntervencionJuridicosForm(
        data={
            "intervencion_juridicos": "rechazado",
            "rechazo_juridicos_motivo": "dictamen",
            "dictamen_motivo": "",
        }
    )

    assert not form.is_valid()
    assert "dictamen_motivo" in form.errors


@pytest.mark.django_db
def test_intervencion_juridicos_form_valido_cuando_rechazado_completo():
    """Con motivo y dictamen completos, el formulario es válido."""
    form = IntervencionJuridicosForm(
        data={
            "intervencion_juridicos": "rechazado",
            "rechazo_juridicos_motivo": "dictamen",
            "dictamen_motivo": "observacion en informe técnico",
        }
    )

    assert form.is_valid()
