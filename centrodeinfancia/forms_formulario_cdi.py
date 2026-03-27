"""Forms para FormularioCDI."""

from __future__ import annotations

from django import forms
from django.forms import inlineformset_factory

from core.models import Localidad, Municipio, Provincia
from centrodeinfancia.formulario_cdi_schema import (
    ARTICULATION_INSTITUTION_OPTIONS,
    BOOLEAN_LABELS,
    CHOICE_FIELDS,
    FIELD_LABELS,
    FORMULARIO_CDI_SECTIONS,
    MULTI_CHOICE_FIELDS,
    ROOM_AGE_GROUP_OPTIONS,
    WAITLIST_AGE_GROUP_OPTIONS,
)
from centrodeinfancia.formulario_cdi_text_overrides import (
    CHOICE_LABEL_OVERRIDES,
    FIELD_LABEL_OVERRIDES,
    MULTI_CHOICE_LABEL_OVERRIDES,
)
from centrodeinfancia.models import (
    FormularioCDI,
    FormularioCDIArticulationFrequency,
    FormularioCDIRoomDistribution,
    FormularioCDIWaitlistByAgeGroup,
)


BOOLEAN_CHOICES = [("", "---------"), ("true", "Si"), ("false", "No")]


def build_fixed_initial_rows(options, key_name):
    return [{key_name: option[0]} for option in options]


class NullableBooleanChoiceField(forms.TypedChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("choices", BOOLEAN_CHOICES)
        kwargs.setdefault("required", False)
        kwargs.setdefault(
            "coerce",
            lambda value: (
                True
                if value in (True, "true", "True", "1", 1)
                else False if value in (False, "false", "False", "0", 0) else None
            ),
        )
        super().__init__(*args, **kwargs)


class FormularioCDIForm(forms.ModelForm):
    operation_months = forms.MultipleChoiceField(
        required=False,
        choices=MULTI_CHOICE_FIELDS["operation_months"],
        widget=forms.CheckboxSelectMultiple,
    )
    operation_days = forms.MultipleChoiceField(
        required=False,
        choices=MULTI_CHOICE_FIELDS["operation_days"],
        widget=forms.CheckboxSelectMultiple,
    )
    health_protocol_items = forms.MultipleChoiceField(
        required=False,
        choices=MULTI_CHOICE_FIELDS["health_protocol_items"],
        widget=forms.CheckboxSelectMultiple,
    )
    meals_provided = forms.MultipleChoiceField(
        required=False,
        choices=MULTI_CHOICE_FIELDS["meals_provided"],
        widget=forms.CheckboxSelectMultiple,
    )
    exclusive_space_use = NullableBooleanChoiceField(
        choices=[
            ("", "---------"),
            ("true", "Sí"),
            ("false", BOOLEAN_LABELS["exclusive_space_use"][1]),
        ]
    )
    has_fire_extinguishers_current = NullableBooleanChoiceField()
    has_working_computer = NullableBooleanChoiceField()
    has_admission_prioritization_tool = NullableBooleanChoiceField()

    class Meta:
        model = FormularioCDI
        exclude = (
            "centro",
            "source_form_version",
            "created_at",
            "updated_at",
            "created_by",
            "deleted_at",
            "deleted_by",
        )
        labels = FIELD_LABELS
        widgets = {
            "survey_date": forms.DateInput(attrs={"type": "date"}),
            "opening_time": forms.TimeInput(attrs={"type": "time"}),
            "closing_time": forms.TimeInput(attrs={"type": "time"}),
            "respondent_full_name": forms.TextInput(attrs={"maxlength": 255}),
            "respondent_role": forms.TextInput(attrs={"maxlength": 255}),
            "cdi_code": forms.TextInput(attrs={"readonly": "readonly"}),
        }

    section_definitions = FORMULARIO_CDI_SECTIONS

    @staticmethod
    def _parse_pk(value):
        if hasattr(value, "pk"):
            return value.pk
        return int(value) if value and str(value).isdigit() else None

    def _get_bound_or_initial(self, field_name, instance_value=None):
        if self.is_bound:
            bound_value = self.data.get(self.add_prefix(field_name))
            if bound_value not in (None, ""):
                return bound_value
        initial_value = self.initial.get(field_name)
        if initial_value not in (None, ""):
            return initial_value
        return instance_value

    def _configure_geo_group(self, prefix):
        province_field = f"{prefix}_province"
        municipality_field = f"{prefix}_municipality"
        locality_field = f"{prefix}_locality"

        province_instance = getattr(self.instance, province_field, None)
        municipality_instance = getattr(self.instance, municipality_field, None)
        locality_instance = getattr(self.instance, locality_field, None)

        province_value = self._get_bound_or_initial(province_field, province_instance)
        municipality_value = self._get_bound_or_initial(
            municipality_field, municipality_instance
        )
        locality_value = self._get_bound_or_initial(locality_field, locality_instance)

        province = Provincia.objects.filter(pk=self._parse_pk(province_value)).first()
        municipality = Municipio.objects.filter(
            pk=self._parse_pk(municipality_value)
        ).first()
        locality = Localidad.objects.filter(pk=self._parse_pk(locality_value)).first()

        self.fields[province_field].queryset = Provincia.objects.all().order_by(
            "nombre"
        )
        self.fields[municipality_field].queryset = (
            Municipio.objects.filter(provincia=province).order_by("nombre")
            if province
            else Municipio.objects.none()
        )
        self.fields[locality_field].queryset = (
            Localidad.objects.filter(municipio=municipality).order_by("nombre")
            if municipality
            else Localidad.objects.none()
        )

        if province:
            self.fields[province_field].initial = province
        if municipality:
            self.fields[municipality_field].initial = municipality
        if locality:
            self.fields[locality_field].initial = locality

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["cdi_code"].disabled = True
        self._configure_geo_group("cdi")
        self._configure_geo_group("org")

        for field_name, options in CHOICE_FIELDS.items():
            if field_name in self.fields:
                choices = [("", "---------"), *options]
                label_overrides = CHOICE_LABEL_OVERRIDES.get(field_name, {})
                if label_overrides:
                    choices = [
                        (value, label_overrides.get(value, label))
                        for value, label in choices
                    ]
                self.fields[field_name].choices = choices

        for field_name, overrides in MULTI_CHOICE_LABEL_OVERRIDES.items():
            if field_name in self.fields:
                self.fields[field_name].choices = [
                    (value, overrides.get(value, label))
                    for value, label in self.fields[field_name].choices
                ]

        for field_name, label in FIELD_LABELS.items():
            if field_name in self.fields:
                self.fields[field_name].label = label

        for field_name, label in FIELD_LABEL_OVERRIDES.items():
            if field_name in self.fields:
                self.fields[field_name].label = label

        for field_name in self.fields:
            field = self.fields[field_name]
            existing = field.widget.attrs.get("class", "")
            if isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs["class"] = f"{existing} form-check-input".strip()
                continue
            widget_class = (
                "form-select"
                if isinstance(
                    field.widget,
                    (forms.Select, forms.SelectMultiple),
                )
                else "form-control"
            )
            field.widget.attrs["class"] = f"{existing} {widget_class}".strip()

    def clean(self):
        cleaned_data = super().clean()
        meals = cleaned_data.get("meals_provided") or []

        # Los campos ocultos por la UI no deben bloquear el guardado si
        # quedaron con valores residuales de una interacción previa.
        if cleaned_data.get("workday_type") != "other":
            cleaned_data["workday_type_other"] = ""

        if cleaned_data.get("management_mode") != "otra":
            cleaned_data["management_mode_other"] = ""

        if cleaned_data.get("tenure_mode") != "otra":
            cleaned_data["tenure_mode_other"] = ""

        if "otra" not in meals:
            cleaned_data["meals_provided_other"] = ""

        if "ninguna" in meals:
            cleaned_data["menu_preparation_quality"] = ""
            cleaned_data["menu_periodic_evaluation"] = ""
            cleaned_data["food_handling_training_coverage"] = ""

        if cleaned_data.get("has_kitchen_space") != "si":
            cleaned_data["cooking_fuel"] = ""

        if cleaned_data.get("has_outdoor_space") != "si":
            cleaned_data["has_outdoor_playground"] = ""

        if cleaned_data.get("electricity_access") == "sin_electricidad":
            cleaned_data["electrical_safety"] = ""

        if self.instance and self.instance.pk:
            cleaned_data["cdi_code"] = self.instance.cdi_code

        return cleaned_data


class FixedRowLabelMixin:
    row_code_field = ""
    row_options = ()

    @property
    def row_label(self):
        option_map = dict(self.row_options)
        value = self.initial.get(self.row_code_field) or self.data.get(
            self.add_prefix(self.row_code_field)
        )
        return option_map.get(value, value)


class FormularioCDIRoomDistributionForm(FixedRowLabelMixin, forms.ModelForm):
    row_code_field = "age_group"
    row_options = ROOM_AGE_GROUP_OPTIONS

    class Meta:
        model = FormularioCDIRoomDistribution
        fields = [
            "age_group",
            "room_count",
            "exclusive_area_m2",
            "children_count",
            "staff_count",
        ]
        widgets = {
            "age_group": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in [
            "room_count",
            "exclusive_area_m2",
            "children_count",
            "staff_count",
        ]:
            self.fields[field_name].required = False
            self.fields[field_name].widget.attrs["class"] = "form-control"


class FormularioCDIWaitlistByAgeGroupForm(FixedRowLabelMixin, forms.ModelForm):
    row_code_field = "age_group"
    row_options = WAITLIST_AGE_GROUP_OPTIONS

    class Meta:
        model = FormularioCDIWaitlistByAgeGroup
        fields = ["age_group", "waitlist_count"]
        widgets = {
            "age_group": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["waitlist_count"].required = False
        self.fields["waitlist_count"].widget.attrs["class"] = "form-control"


class FormularioCDIArticulationFrequencyForm(FixedRowLabelMixin, forms.ModelForm):
    row_code_field = "institution_type"
    row_options = ARTICULATION_INSTITUTION_OPTIONS

    class Meta:
        model = FormularioCDIArticulationFrequency
        fields = ["institution_type", "frequency"]
        widgets = {
            "institution_type": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["frequency"].required = False
        self.fields["frequency"].widget.attrs["class"] = "form-select"


def build_room_distribution_formset_class(extra=0):
    return inlineformset_factory(
        FormularioCDI,
        FormularioCDIRoomDistribution,
        form=FormularioCDIRoomDistributionForm,
        extra=extra,
        can_delete=False,
    )


def build_waitlist_formset_class(extra=0):
    return inlineformset_factory(
        FormularioCDI,
        FormularioCDIWaitlistByAgeGroup,
        form=FormularioCDIWaitlistByAgeGroupForm,
        extra=extra,
        can_delete=False,
    )


def build_articulation_formset_class(extra=0):
    return inlineformset_factory(
        FormularioCDI,
        FormularioCDIArticulationFrequency,
        form=FormularioCDIArticulationFrequencyForm,
        extra=extra,
        can_delete=False,
    )
