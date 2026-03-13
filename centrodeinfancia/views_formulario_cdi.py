"""CRUD web para FormularioCDI."""

from __future__ import annotations

from collections import OrderedDict

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView

from centrodeinfancia.access import aplicar_filtro_provincia_usuario
from centrodeinfancia.forms import (
    FormularioCDIForm,
    build_fixed_initial_rows,
    build_articulation_formset_class,
    build_room_distribution_formset_class,
    build_waitlist_formset_class,
)
from centrodeinfancia.formulario_cdi_schema import (
    ARTICULATION_INSTITUTION_OPTIONS,
    CHOICE_FIELDS,
    FIELD_LABELS,
    FORMULARIO_CDI_SECTIONS,
    MULTI_CHOICE_FIELDS,
    ROOM_AGE_GROUP_OPTIONS,
    WAITLIST_AGE_GROUP_OPTIONS,
)
from centrodeinfancia.models import (
    CentroDeInfancia,
    FormularioCDI,
    FormularioCDIArticulationFrequency,
    FormularioCDIRoomDistribution,
    FormularioCDIWaitlistByAgeGroup,
)

FULL_WIDTH_FIELD_NAMES = {"health_protocol_items", "meals_provided"}
FORCED_FIELD_ROWS = {
    "operation_months": ("operation_months", "operation_days"),
}


def _formularios_cdi_queryset_scoped(user):
    queryset = FormularioCDI.objects.select_related(
        "centro",
        "created_by",
        "cdi_province",
        "cdi_municipality",
        "cdi_locality",
        "org_province",
        "org_municipality",
        "org_locality",
    )
    return aplicar_filtro_provincia_usuario(
        queryset, user, provincia_lookup="centro__provincia"
    )


def _get_centro_scoped_or_404(user, pk):
    queryset = CentroDeInfancia.objects.select_related(
        "organizacion", "provincia", "municipio", "localidad"
    )
    queryset = aplicar_filtro_provincia_usuario(queryset, user)
    return get_object_or_404(queryset, pk=pk)


def _get_formulario_scoped_or_404(user, centro_id, form_pk):
    queryset = _formularios_cdi_queryset_scoped(user).filter(centro_id=centro_id)
    return get_object_or_404(queryset, pk=form_pk)


def _choice_map_for(field_name):
    if field_name in CHOICE_FIELDS:
        return dict(CHOICE_FIELDS[field_name])
    if field_name in MULTI_CHOICE_FIELDS:
        return dict(MULTI_CHOICE_FIELDS[field_name])
    return {}


def _display_value(obj, field_name):
    value = getattr(obj, field_name, None)
    if value in (None, "", []):
        return "-"

    if hasattr(value, "strftime"):
        if field_name.endswith("_time"):
            return value.strftime("%H:%M")
        if field_name.endswith("_date") or "date" in field_name:
            return value.strftime("%d/%m/%Y")
        return value.strftime("%d/%m/%Y %H:%M")

    if isinstance(value, bool):
        return "Si" if value else "No"

    if isinstance(value, list):
        option_map = _choice_map_for(field_name)
        return ", ".join(option_map.get(item, item) for item in value) or "-"

    option_map = _choice_map_for(field_name)
    if option_map:
        return option_map.get(value, value)

    return str(value)


def build_formulario_summary_items(formularios):
    items = []
    for formulario in formularios:
        items.append(
            {
                "id": formulario.id,
                "survey_date": formulario.survey_date,
                "respondent_full_name": formulario.respondent_full_name or "-",
                "created_at": formulario.created_at,
                "updated_at": formulario.updated_at,
                "detail_url": reverse(
                    "centrodeinfancia_formulario_detalle",
                    kwargs={"pk": formulario.centro_id, "form_pk": formulario.pk},
                ),
                "edit_url": reverse(
                    "centrodeinfancia_formulario_editar",
                    kwargs={"pk": formulario.centro_id, "form_pk": formulario.pk},
                ),
            }
        )
    return items


class FormularioCDIListView(LoginRequiredMixin, ListView):
    model = FormularioCDI
    template_name = "centrodeinfancia/formulario_cdi_list.html"
    context_object_name = "formularios"
    paginate_by = 10

    def get_centro(self):
        if not hasattr(self, "_centro_cache"):
            self._centro_cache = _get_centro_scoped_or_404(
                self.request.user, self.kwargs["pk"]
            )
        return self._centro_cache

    def get_queryset(self):
        return _formularios_cdi_queryset_scoped(self.request.user).filter(
            centro_id=self.kwargs["pk"]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        centro = self.get_centro()
        context["centro"] = centro
        context["summary_items"] = build_formulario_summary_items(
            context["object_list"]
        )
        page_obj = context.get("page_obj")
        if page_obj:
            context["page_range"] = context["paginator"].get_elided_page_range(
                number=page_obj.number
            )
        return context


class FormularioCDIDetailView(LoginRequiredMixin, DetailView):
    model = FormularioCDI
    template_name = "centrodeinfancia/formulario_cdi_detail.html"
    context_object_name = "formulario"
    pk_url_kwarg = "form_pk"

    def get_queryset(self):
        return _formularios_cdi_queryset_scoped(self.request.user).filter(
            centro_id=self.kwargs["pk"]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["centro"] = self.object.centro
        context["detail_sections"] = self._build_detail_sections(self.object)
        context["room_rows"] = self.object.room_distribution_rows.order_by("id")
        context["waitlist_rows"] = self.object.waitlist_rows.order_by("id")
        context["articulation_rows"] = self.object.articulation_rows.order_by("id")
        context["room_totals"] = self._sum_numeric_rows(
            context["room_rows"],
            ["room_count", "exclusive_area_m2", "children_count", "staff_count"],
        )
        context["waitlist_total"] = sum(
            item.waitlist_count or 0 for item in context["waitlist_rows"]
        )
        return context

    @staticmethod
    def _sum_numeric_rows(rows, field_names):
        totals = OrderedDict()
        for field_name in field_names:
            totals[field_name] = sum(getattr(item, field_name) or 0 for item in rows)
        return totals

    @staticmethod
    def _build_detail_sections(formulario):
        sections = []
        for section in FORMULARIO_CDI_SECTIONS:
            items = []
            for field_name in section["fields"]:
                items.append(
                    {
                        "label": FIELD_LABELS.get(field_name, field_name),
                        "value": _display_value(formulario, field_name),
                    }
                )
            sections.append({"title": section["title"], "items": items})
        return sections


class FormularioCDIEditBaseView(LoginRequiredMixin, View):
    template_name = "centrodeinfancia/formulario_cdi_form.html"
    form_class = FormularioCDIForm

    def get_centro(self):
        return _get_centro_scoped_or_404(self.request.user, self.kwargs["pk"])

    def get_form_instance(self):
        return None

    def get_initial(self):
        centro = self.get_centro()
        return {
            "cdi_name": centro.nombre,
            "cdi_code": centro.cdi_code,
            "cdi_province": centro.provincia,
            "cdi_municipality": centro.municipio,
            "cdi_locality": centro.localidad,
            "cdi_street": centro.calle,
            "cdi_door_number": centro.numero,
            "cdi_phone": centro.telefono,
            "cdi_contact_first_name": centro.nombre_referente,
            "cdi_contact_last_name": centro.apellido_referente,
            "cdi_contact_phone": centro.telefono_referente,
            "cdi_contact_email": centro.email_referente,
        }

    def build_form(self, data=None, instance=None):
        return self.form_class(data=data, instance=instance, initial=self.get_initial())

    def build_formsets(self, data=None, instance=None):
        if instance and instance.pk:
            self.ensure_fixed_rows(instance)

        room_formset_class = build_room_distribution_formset_class(
            0 if instance and instance.pk else len(ROOM_AGE_GROUP_OPTIONS)
        )
        waitlist_formset_class = build_waitlist_formset_class(
            0 if instance and instance.pk else len(WAITLIST_AGE_GROUP_OPTIONS)
        )
        articulation_formset_class = build_articulation_formset_class(
            0 if instance and instance.pk else len(ARTICULATION_INSTITUTION_OPTIONS)
        )

        room_initial = (
            []
            if instance
            else build_fixed_initial_rows(ROOM_AGE_GROUP_OPTIONS, "age_group")
        )
        waitlist_initial = (
            []
            if instance
            else build_fixed_initial_rows(WAITLIST_AGE_GROUP_OPTIONS, "age_group")
        )
        articulation_initial = (
            []
            if instance
            else build_fixed_initial_rows(
                ARTICULATION_INSTITUTION_OPTIONS, "institution_type"
            )
        )
        formsets = {
            "room_formset": room_formset_class(
                data=data,
                instance=instance or FormularioCDI(),
                prefix="room_distribution",
                initial=room_initial,
            ),
            "waitlist_formset": waitlist_formset_class(
                data=data,
                instance=instance or FormularioCDI(),
                prefix="waitlist_by_age_group",
                initial=waitlist_initial,
            ),
            "articulation_formset": articulation_formset_class(
                data=data,
                instance=instance or FormularioCDI(),
                prefix="articulation_frequency",
                initial=articulation_initial,
            ),
        }
        return formsets

    @staticmethod
    def build_form_sections(form):
        sections = []
        for section in form.section_definitions:
            rows = []
            field_names = section["fields"]
            forced_row_starts = set(FORCED_FIELD_ROWS)
            index = 0

            while index < len(field_names):
                current_name = field_names[index]
                forced_row = FORCED_FIELD_ROWS.get(current_name)

                if (
                    forced_row
                    and tuple(field_names[index : index + len(forced_row)])
                    == forced_row
                ):
                    rows.append(
                        [
                            {
                                "bound_field": form[field_name],
                                "name": field_name,
                                "col_class": "col-md-6",
                            }
                            for field_name in forced_row
                        ]
                    )
                    index += len(forced_row)
                    continue

                if current_name in FULL_WIDTH_FIELD_NAMES:
                    rows.append(
                        [
                            {
                                "bound_field": form[current_name],
                                "name": current_name,
                                "col_class": "col-12",
                            }
                        ]
                    )
                    index += 1
                    continue

                current_field = {
                    "bound_field": form[current_name],
                    "name": current_name,
                    "col_class": "col-md-6",
                }
                next_name = (
                    field_names[index + 1] if index + 1 < len(field_names) else None
                )

                if (
                    next_name
                    and next_name not in FULL_WIDTH_FIELD_NAMES
                    and next_name not in forced_row_starts
                ):
                    rows.append(
                        [
                            current_field,
                            {
                                "bound_field": form[next_name],
                                "name": next_name,
                                "col_class": "col-md-6",
                            },
                        ]
                    )
                    index += 2
                    continue

                rows.append([current_field])
                index += 1

            sections.append(
                {
                    "title": section["title"],
                    "rows": rows,
                }
            )
        return sections

    def get_context(self, form, formsets, instance=None):
        centro = self.get_centro()
        return {
            "form": form,
            "centro": centro,
            "section_fields": self.build_form_sections(form),
            "room_formset": formsets["room_formset"],
            "waitlist_formset": formsets["waitlist_formset"],
            "articulation_formset": formsets["articulation_formset"],
            "is_edit": bool(instance and instance.pk),
        }

    @staticmethod
    def ensure_fixed_rows(formulario):
        room_existing = set(
            formulario.room_distribution_rows.values_list("age_group", flat=True)
        )
        waitlist_existing = set(
            formulario.waitlist_rows.values_list("age_group", flat=True)
        )
        articulation_existing = set(
            formulario.articulation_rows.values_list("institution_type", flat=True)
        )

        for value, _label in ROOM_AGE_GROUP_OPTIONS:
            if value not in room_existing:
                FormularioCDIRoomDistribution.objects.create(
                    formulario=formulario,
                    age_group=value,
                )

        for value, _label in WAITLIST_AGE_GROUP_OPTIONS:
            if value not in waitlist_existing:
                FormularioCDIWaitlistByAgeGroup.objects.create(
                    formulario=formulario,
                    age_group=value,
                )

        for value, _label in ARTICULATION_INSTITUTION_OPTIONS:
            if value not in articulation_existing:
                FormularioCDIArticulationFrequency.objects.create(
                    formulario=formulario,
                    institution_type=value,
                )

    def get(self, request, *args, **kwargs):
        instance = self.get_form_instance()
        form = self.build_form(instance=instance)
        formsets = self.build_formsets(instance=instance)
        return render(
            request, self.template_name, self.get_context(form, formsets, instance)
        )

    def post(self, request, *args, **kwargs):
        instance = self.get_form_instance()
        form = self.build_form(data=request.POST, instance=instance)
        formsets = self.build_formsets(data=request.POST, instance=instance)

        if form.is_valid() and all(formset.is_valid() for formset in formsets.values()):
            with transaction.atomic():
                formulario = form.save(commit=False)
                formulario.centro = self.get_centro()
                if not formulario.pk:
                    formulario.created_by = request.user
                formulario.save()
                for formset in formsets.values():
                    formset.instance = formulario
                    formset.save()
                self.ensure_fixed_rows(formulario)

            messages.success(request, self.get_success_message(formulario))
            return redirect(
                "centrodeinfancia_formulario_detalle",
                pk=formulario.centro_id,
                form_pk=formulario.pk,
            )

        return render(
            request,
            self.template_name,
            self.get_context(form, formsets, instance),
        )

    def get_success_message(self, formulario):
        return f"Formulario #{formulario.pk} guardado correctamente."


class FormularioCDICreateView(FormularioCDIEditBaseView):
    def get_success_message(self, formulario):
        return f"Formulario #{formulario.pk} creado correctamente."


class FormularioCDIUpdateView(FormularioCDIEditBaseView):
    def get_form_instance(self):
        return _get_formulario_scoped_or_404(
            self.request.user,
            self.kwargs["pk"],
            self.kwargs["form_pk"],
        )

    def get_success_message(self, formulario):
        return f"Formulario #{formulario.pk} actualizado correctamente."
