"""Unit tests for helpers and forms in admisiones forms module."""

from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from admisiones.forms.admisiones_forms import (
    ConvenioForm,
    ConvenioNumIFFORM,
    DisposicionForm,
    DisposicionNumIFFORM,
    DocumentosExpedienteForm,
    IFInformeTecnicoForm,
    IntervencionJuridicosForm,
    InformeTecnicoBaseForm,
    InformeTecnicoEstadoForm,
    InformeTecnicoJuridicoForm,
    InformeSGAForm,
    LegalesNumIFForm,
    LegalesRectificarForm,
    MontoDecimalField,
    ProyectoConvenioForm,
    ProyectoDisposicionForm,
    ReinicioExpedienteForm,
    SolicitarInformeComplementarioForm,
    _armar_domicilio,
    _permite_no_corresponde_fecha_vencimiento,
    _prellenar_campos_gde,
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


class _FormStub:
    """Formulario mínimo: lo que `_prellenar_campos_gde` necesita tocar."""

    def __init__(self, fields, initial=None, instance=None):
        self.fields = fields
        self.initial = dict(initial or {})
        self.instance = instance


def _informe(pk=1, estado="Iniciado", estado_formulario="borrador"):
    return SimpleNamespace(pk=pk, estado=estado, estado_formulario=estado_formulario)


def test_prellenar_campos_gde_setea_iniciales(mocker):
    """Aplica el mapeo documento -> campo sobre los campos expuestos."""
    mocker.patch(
        "admisiones.forms.admisiones_forms.numeros_gde_por_campo_de_informe",
        return_value={"if_relevamiento": "GDE-XYZ", "nota_gde_if": "GDE-NOTA"},
    )
    form = _FormStub(
        {
            "if_relevamiento": SimpleNamespace(initial=None),
            "nota_gde_if": SimpleNamespace(initial=None),
        },
        instance=_informe(),
    )

    _prellenar_campos_gde(form, admision=object(), tipo_informe="base")

    assert form.fields["if_relevamiento"].initial == "GDE-XYZ"
    assert form.fields["nota_gde_if"].initial == "GDE-NOTA"


def test_prellenar_campos_gde_escribe_en_form_initial(mocker):
    """Regresión: `fields[].initial` no alcanza sobre una instancia guardada.

    Django arma `form.initial` desde la instancia, así que el valor del
    documento tiene que escribirse ahí para poder ganarle al valor guardado.
    """
    mocker.patch(
        "admisiones.forms.admisiones_forms.numeros_gde_por_campo_de_informe",
        return_value={"nota_gde_if": "GDE-DOCUMENTO"},
    )
    form = _FormStub(
        {"nota_gde_if": SimpleNamespace(initial=None)},
        initial={"nota_gde_if": "GDE-GUARDADO-VIEJO"},
        instance=_informe(),
    )

    _prellenar_campos_gde(form, admision=object(), tipo_informe="base")

    assert form.initial["nota_gde_if"] == "GDE-DOCUMENTO"


def test_prellenar_campos_gde_no_toca_informe_finalizado(mocker):
    """Un informe finalizado conserva sus valores."""
    mocker.patch(
        "admisiones.forms.admisiones_forms.numeros_gde_por_campo_de_informe",
        return_value={"nota_gde_if": "GDE-DOCUMENTO"},
    )
    form = _FormStub(
        {"nota_gde_if": SimpleNamespace(initial=None)},
        initial={"nota_gde_if": "GDE-FINAL"},
        instance=_informe(estado="Validado", estado_formulario="finalizado"),
    )

    _prellenar_campos_gde(form, admision=object(), tipo_informe="base")

    assert form.initial["nota_gde_if"] == "GDE-FINAL"


def test_prellenar_campos_gde_aplica_a_informe_nuevo(mocker):
    """Un informe todavía sin guardar también arrastra el GDE."""
    mocker.patch(
        "admisiones.forms.admisiones_forms.numeros_gde_por_campo_de_informe",
        return_value={"nota_gde_if": "GDE-DOCUMENTO"},
    )
    form = _FormStub(
        {"nota_gde_if": SimpleNamespace(initial=None)},
        instance=SimpleNamespace(pk=None, estado=None, estado_formulario=None),
    )

    _prellenar_campos_gde(form, admision=object(), tipo_informe="base")

    assert form.initial["nota_gde_if"] == "GDE-DOCUMENTO"


def test_prellenar_campos_gde_ignora_campos_no_expuestos(mocker):
    """Un campo que el formulario no declara no debe romper el prellenado."""
    mocker.patch(
        "admisiones.forms.admisiones_forms.numeros_gde_por_campo_de_informe",
        return_value={"IF_relevamiento_territorial": "GDE-XYZ"},
    )
    form = _FormStub(
        {"if_relevamiento": SimpleNamespace(initial="ORIGINAL")},
        instance=_informe(),
    )

    _prellenar_campos_gde(form, admision=object(), tipo_informe="base")

    assert form.fields["if_relevamiento"].initial == "ORIGINAL"
    assert "IF_relevamiento_territorial" not in form.initial


def test_prellenar_campos_gde_no_consulta_sin_admision(mocker):
    """Sin admisión no toca campos ni consulta la base."""
    spy = mocker.patch(
        "admisiones.forms.admisiones_forms.numeros_gde_por_campo_de_informe"
    )
    form = _FormStub(
        {"if_relevamiento": SimpleNamespace(initial="ORIGINAL")},
        instance=_informe(),
    )

    _prellenar_campos_gde(form, admision=None, tipo_informe="base")

    assert form.fields["if_relevamiento"].initial == "ORIGINAL"
    spy.assert_not_called()


def test_informe_tecnico_juridico_clean_error_si_no_corresponde_invalido(mocker):
    """Agrega error cuando se marca no corresponde y el convenio no lo permite."""
    form = InformeTecnicoJuridicoForm()
    form.permite_no_corresponde_fecha_vencimiento = False
    form.require_full = False
    form.cleaned_data = {}

    mocker.patch(
        "django.forms.models.BaseModelForm.clean",
        return_value={
            "no_corresponde_fecha_vencimiento": True,
            "fecha_vencimiento_mandatos": None,
        },
    )

    cleaned = form.clean()

    assert "no_corresponde_fecha_vencimiento" in form.errors
    assert cleaned["fecha_vencimiento_mandatos"] is None


def test_informe_tecnico_juridico_clean_exige_fecha_o_check_si_require_full(mocker):
    """Exige fecha o marcar no corresponde cuando el flujo es completo."""
    form = InformeTecnicoJuridicoForm()
    form.permite_no_corresponde_fecha_vencimiento = True
    form.require_full = True
    form.cleaned_data = {}

    mocker.patch(
        "django.forms.models.BaseModelForm.clean",
        return_value={
            "no_corresponde_fecha_vencimiento": False,
            "fecha_vencimiento_mandatos": None,
        },
    )

    form.clean()

    assert "fecha_vencimiento_mandatos" in form.errors


def test_informe_tecnico_base_clean_setea_fecha_none_si_no_corresponde(mocker):
    """Al marcar no corresponde, limpia la fecha en el formulario base."""
    form = InformeTecnicoBaseForm()
    form.permite_no_corresponde_fecha_vencimiento = True
    form.require_full = False
    form.cleaned_data = {}

    mocker.patch(
        "django.forms.models.BaseModelForm.clean",
        return_value={
            "no_corresponde_fecha_vencimiento": True,
            "fecha_vencimiento_mandatos": "2030-01-01",
        },
    )

    cleaned = form.clean()

    assert cleaned["fecha_vencimiento_mandatos"] is None


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
def test_legales_num_if_form_precarga_y_permite_rectificar():
    """Precarga las partes del expediente y permite rectificarlas."""
    admision = Admision(
        num_expediente="EX-2025-112100154- -APN-DDNAYF#MCH",
        legales_num_if="",
    )

    form = LegalesNumIFForm(instance=admision)

    assert form.initial["expediente_anio"] == "2025"
    assert form.initial["expediente_numero"] == "112100154"
    assert form.initial["expediente_reparticion"] == "DDNAYF"
    assert form.initial["expediente_organismo"] == "MCH"
    assert all(not field.disabled for field in form.fields.values())


def test_numero_expediente_campos_son_editables_y_responsivos():
    form = LegalesNumIFForm(instance=Admision())

    assert form.fields["expediente_anio"].widget.attrs == {
        "class": "form-control",
        "inputmode": "numeric",
        "autocomplete": "off",
        "placeholder": "2025",
        "maxlength": "4",
        "minlength": "4",
    }
    assert form.fields["expediente_numero"].widget.attrs["inputmode"] == "numeric"
    assert form.fields["expediente_numero"].widget.attrs["placeholder"] == "112100154"
    assert (
        "text-uppercase" in form.fields["expediente_reparticion"].widget.attrs["class"]
    )


def test_modales_expediente_usan_layout_amplio_y_parcial_compartido():
    tecnicos = Path(
        "admisiones/templates/admisiones/admisiones_tecnicos_form.html"
    ).read_text(encoding="utf-8")
    legales = Path(
        "admisiones/templates/admisiones/admisiones_legales_detalle.html"
    ).read_text(encoding="utf-8")

    assert tecnicos.count("modal-expediente-amplio") == 2
    assert "modal-expediente-amplio" in legales
    assert (
        "modal-xl"
        not in tecnicos.split('id="caratularExpediente"', maxsplit=1)[1].split(
            '<div class="modal-content">', maxsplit=1
        )[0]
    )
    modal_editar = tecnicos.split('id="editarExpedienteModal"', maxsplit=1)[1]
    assert (
        "modal-dialog-centered modal-expediente-amplio"
        in modal_editar.split('<div class="modal-content">', maxsplit=1)[0]
    )
    modal_legales = legales.split('id="modalLegalesNumIF"', maxsplit=1)[1]
    assert (
        "modal-expediente-amplio"
        in modal_legales.split('<div class="modal-content">', maxsplit=1)[0]
    )
    assert "numero_expediente_form=caratular_form" in tecnicos
    assert "numero_expediente_form=form_legales_num_if" in legales


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


@pytest.mark.parametrize(
    "form_class",
    [
        LegalesRectificarForm,
        ProyectoDisposicionForm,
        ProyectoConvenioForm,
        DocumentosExpedienteForm,
        ConvenioNumIFFORM,
        DisposicionNumIFFORM,
        InformeSGAForm,
        ConvenioForm,
        DisposicionForm,
        IFInformeTecnicoForm,
        ReinicioExpedienteForm,
        SolicitarInformeComplementarioForm,
    ],
)
def test_forms_marcan_todos_los_campos_como_obligatorios(form_class):
    """Los formularios operativos de flujo legal/tecnico deben marcar required=True."""
    form = form_class()
    assert all(field.required for field in form.fields.values())


def test_documentos_expediente_form_label_vacio_en_value():
    """El label de value debe quedar vacío para render de tabla."""
    form = DocumentosExpedienteForm()
    assert form.fields["value"].label == ""


def test_convenio_y_disposicion_num_if_labels_configurados():
    """Verifica labels explícitos de formularios de número IF."""
    form_convenio = ConvenioNumIFFORM()
    form_disposicion = DisposicionNumIFFORM()

    assert "Proyecto de Convenio" in form_convenio.fields["numero_if"].label
    assert "Proyecto Disposición" in form_disposicion.fields["numero_if"].label
