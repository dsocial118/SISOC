"""Formularios del backoffice para el ciclo de seguimiento y las actas
complementarias.

Hasta ahora estos registros solo se cargaban desde la app; el backoffice los
mostraba en modo lectura. Acá se arma la edición completa: un formulario raíz
por instancia, un ``ModelForm`` por bloque (los mismos ``BLOQUES_SEGUIMIENTO``
que consume la app) y formsets para las tablas hijas (prestaciones).
"""

from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction
from django.forms import inlineformset_factory, modelform_factory

from relevamientos.models import (
    BLOQUES_SEGUIMIENTO,
    ActaComplementaria,
    PrestacionActaComplementaria,
    PrestacionSeguimiento,
    PrimerSeguimiento,
)

FECHA_HORA_WIDGET = forms.DateTimeInput(
    attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
)


def aplicar_clases_bootstrap(form):
    """Agrega las clases de Bootstrap a los widgets para que los formularios
    generados con ``modelform_factory`` se vean como el resto del sistema."""
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, forms.CheckboxInput):
            css = "form-check-input"
        elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
            css = "form-select"
        else:
            css = "form-control"
        actual = widget.attrs.get("class", "")
        widget.attrs["class"] = f"{actual} {css}".strip()
    return form


class BootstrapModelForm(forms.ModelForm):
    """Base para los formularios generados dinámicamente."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        aplicar_clases_bootstrap(self)


# --------------------------------------------------------------------------- #
# Instancias del ciclo de seguimiento
# --------------------------------------------------------------------------- #


class SeguimientoRootForm(BootstrapModelForm):
    """Campos propios de la instancia (no de sus bloques).

    ``referente`` se excluye a propósito: es una FK a todos los referentes del
    sistema y renderizarla como ``<select>`` es inviable en producción.
    """

    class Meta:
        model = PrimerSeguimiento
        fields = (
            "fecha_hora",
            "estado",
            "tecnico",
            "motivo_diferencia_aprobado_declarado",
        )
        widgets = {"fecha_hora": FECHA_HORA_WIDGET}


PrestacionSeguimientoFormSet = inlineformset_factory(
    PrimerSeguimiento,
    PrestacionSeguimiento,
    form=BootstrapModelForm,
    fields=(
        "dias_prestacion",
        "tipo_prestacion",
        "ap_presencial",
        "ap_vianda",
        "de_presencial",
        "de_vianda",
    ),
    extra=1,
    can_delete=True,
)


def _form_class_bloque(model):
    return modelform_factory(model, form=BootstrapModelForm, fields="__all__")


_VALORES_VACIOS = (None, "", "unknown")  # "unknown" = NullBooleanSelect sin elegir


def _bloque_con_datos(form):
    """True si el usuario cargó algo en un bloque que todavía no existe.

    No sirve ``has_changed()``: compara contra los defaults del modelo, con lo
    que un bloque sin tocar cuyo modelo tiene defaults aparecería "cambiado" y
    se crearía vacío.
    """
    if not form.is_bound:
        return False
    for nombre in form.fields:
        clave = form.add_prefix(nombre)
        if hasattr(form.data, "getlist"):
            valores = form.data.getlist(clave)
        else:
            valores = [form.data.get(clave)]
        if any(valor not in _VALORES_VACIOS for valor in valores):
            return True
    return False


class SeguimientoEditor:
    """Agrupa el formulario raíz, un formulario por bloque y el formset de
    prestaciones de una instancia del ciclo.

    Los bloques que la instancia todavía no tiene se crean únicamente si el
    usuario cargó algo en ellos; un bloque vacío no se valida ni se persiste,
    así el coordinador puede completar de a poco.
    """

    def __init__(self, seguimiento, data=None):
        self.seguimiento = seguimiento
        self.root = SeguimientoRootForm(data, instance=seguimiento, prefix="seg")
        self.prestaciones = PrestacionSeguimientoFormSet(
            data, instance=seguimiento, prefix="prestaciones"
        )
        self.bloques = []
        for attr, label in BLOQUES_SEGUIMIENTO:
            model = PrimerSeguimiento._meta.get_field(attr).related_model
            instancia = getattr(seguimiento, attr, None)
            self.bloques.append(
                {
                    "key": attr,
                    "label": label,
                    "existe": instancia is not None,
                    "form": _form_class_bloque(model)(
                        data, instance=instancia, prefix=attr
                    ),
                }
            )

    def _bloques_a_guardar(self):
        for bloque in self.bloques:
            if bloque["existe"] or _bloque_con_datos(bloque["form"]):
                yield bloque

    def es_valido(self):
        formularios = [self.root, self.prestaciones]
        formularios.extend(bloque["form"] for bloque in self._bloques_a_guardar())
        # Se validan todos (no ``all(generator)``) para mostrar cada error.
        resultados = [formulario.is_valid() for formulario in formularios]
        return all(resultados)

    @transaction.atomic
    def guardar(self):
        seguimiento = self.root.save()
        nuevos = []
        for bloque in self._bloques_a_guardar():
            instancia = bloque["form"].save()
            if not bloque["existe"]:
                setattr(seguimiento, bloque["key"], instancia)
                nuevos.append(bloque["key"])
        if nuevos:
            seguimiento.save(update_fields=nuevos)
        self.prestaciones.save()
        return seguimiento


# --------------------------------------------------------------------------- #
# Actas complementarias extraordinarias
# --------------------------------------------------------------------------- #


class ActaComplementariaForm(BootstrapModelForm):
    class Meta:
        model = ActaComplementaria
        fields = ("fecha_hora", "tecnico", "observaciones")
        widgets = {
            "fecha_hora": FECHA_HORA_WIDGET,
            "observaciones": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {"tecnico": "Técnico territorial"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tecnico"].required = False
        self.fields["tecnico"].queryset = (
            get_user_model()
            .objects.filter(is_active=True, profile__es_territorial_comedor=True)
            .order_by("username")
        )
        self.fields["tecnico"].help_text = (
            "Si se deja vacío queda registrado el usuario que carga el acta."
        )


PrestacionActaFormSet = inlineformset_factory(
    ActaComplementaria,
    PrestacionActaComplementaria,
    form=BootstrapModelForm,
    fields=("dias_prestacion", "tipo_prestacion", "cantidad_actual", "cantidad_espera"),
    extra=1,
    can_delete=True,
)


class ActaComplementariaEditor:
    """Alta y edición de un acta con su tabla de prestaciones."""

    def __init__(self, comedor, acta=None, data=None):
        self.acta = acta if acta is not None else ActaComplementaria(comedor=comedor)
        self.form = ActaComplementariaForm(data, instance=self.acta, prefix="acta")
        self.prestaciones = PrestacionActaFormSet(
            data, instance=self.acta, prefix="prestaciones"
        )

    def es_valido(self):
        resultados = [self.form.is_valid(), self.prestaciones.is_valid()]
        return all(resultados)

    @transaction.atomic
    def guardar(self, usuario):
        acta = self.form.save(commit=False)
        if acta.tecnico_id is None:
            acta.tecnico = usuario
        acta.save()
        self.prestaciones.instance = acta
        self.prestaciones.save()
        return acta
