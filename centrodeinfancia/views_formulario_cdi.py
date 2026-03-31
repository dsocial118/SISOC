"""CRUD web para FormularioCDI."""

from __future__ import annotations

from collections import OrderedDict
from datetime import date, datetime, time
from functools import lru_cache

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
    construir_filas_iniciales_fijas,
    construir_clase_formset_articulacion,
    construir_clase_formset_distribucion_salas,
    construir_clase_formset_demanda_insatisfecha,
)
from centrodeinfancia.formulario_cdi_schema import (
    OPCIONES_INSTITUCIONES_ARTICULACION,
    CAMPOS_OPCIONES,
    ETIQUETAS_CAMPOS,
    SECCIONES_FORMULARIO_CDI,
    CAMPOS_OPCIONES_MULTIPLES,
    OPCIONES_GRUPO_ETARIO_SALAS,
    OPCIONES_GRUPO_ETARIO_DEMANDA,
)
from centrodeinfancia.models import (
    CentroDeInfancia,
    FormularioCDI,
    FormularioCDIArticulationFrequency,
    FormularioCDIRoomDistribution,
    FormularioCDIWaitlistByAgeGroup,
)

CAMPOS_ANCHO_COMPLETO = {"items_protocolo_salud", "prestaciones_alimentarias"}
FILAS_FORZADAS = {
    "meses_funcionamiento": ("meses_funcionamiento", "dias_funcionamiento"),
}


def _obtener_queryset_formularios_cdi_filtrado(user):
    queryset = FormularioCDI.objects.select_related(
        "centro",
        "created_by",
        "provincia_cdi",
        "departamento_cdi",
        "municipio_cdi",
        "localidad_cdi",
        "provincia_organizacion",
        "departamento_organizacion",
        "municipio_organizacion",
        "localidad_organizacion",
    )
    return aplicar_filtro_provincia_usuario(
        queryset, user, provincia_lookup="centro__provincia"
    )


def _obtener_centro_filtrado_o_404(user, pk):
    queryset = CentroDeInfancia.objects.select_related(
        "provincia", "departamento", "municipio", "localidad"
    )
    queryset = aplicar_filtro_provincia_usuario(queryset, user)
    return get_object_or_404(queryset, pk=pk)


def _obtener_formulario_filtrado_o_404(user, centro_id, form_pk):
    queryset = _obtener_queryset_formularios_cdi_filtrado(user).filter(
        centro_id=centro_id
    )
    return get_object_or_404(queryset, pk=form_pk)


def _obtener_mapa_opciones(field_name):
    return _obtener_mapas_opciones_formulario().get(field_name, {})


@lru_cache(maxsize=1)
def _obtener_mapas_opciones_formulario():
    form = FormularioCDIForm()
    field_names = set(CAMPOS_OPCIONES) | set(CAMPOS_OPCIONES_MULTIPLES)
    choice_maps = {}
    for field_name in field_names:
        if field_name not in form.fields:
            continue
        choice_maps[field_name] = {
            value: label
            for value, label in form.fields[field_name].choices
            if value not in ("", None)
        }
    return choice_maps


@lru_cache(maxsize=1)
def _obtener_etiquetas_campos_formulario():
    form = FormularioCDIForm()
    return {field_name: field.label for field_name, field in form.fields.items()}


def _mostrar_valor_campo(obj, field_name):
    value = getattr(obj, field_name, None)
    display_value = "-"

    if value not in (None, "", []):
        if isinstance(value, time):
            display_value = value.strftime("%H:%M")
        elif isinstance(value, datetime):
            display_value = value.strftime("%d/%m/%Y %H:%M")
        elif isinstance(value, date):
            display_value = value.strftime("%d/%m/%Y")
        elif isinstance(value, bool):
            display_value = "Si" if value else "No"
        elif isinstance(value, list):
            option_map = _obtener_mapa_opciones(field_name)
            display_value = (
                ", ".join(option_map.get(item, item) for item in value) or "-"
            )
        else:
            option_map = _obtener_mapa_opciones(field_name)
            display_value = option_map.get(value, value) if option_map else str(value)

    return display_value


def construir_resumenes_formularios(formularios):
    items = []
    for formulario in formularios:
        items.append(
            {
                "id": formulario.id,
                "fecha_relevamiento": formulario.fecha_relevamiento,
                "nombre_completo_respondente": formulario.nombre_completo_respondente
                or "-",
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
            self._centro_cache = _obtener_centro_filtrado_o_404(
                self.request.user, self.kwargs["pk"]
            )
        return self._centro_cache

    def get_queryset(self):
        return _obtener_queryset_formularios_cdi_filtrado(self.request.user).filter(
            centro_id=self.kwargs["pk"]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        centro = self.get_centro()
        context["centro"] = centro
        context["summary_items"] = construir_resumenes_formularios(
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
        return _obtener_queryset_formularios_cdi_filtrado(self.request.user).filter(
            centro_id=self.kwargs["pk"]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["centro"] = self.object.centro
        context["detail_sections"] = self._build_detail_sections(self.object)
        context["filas_salas"] = self.object.filas_distribucion_salas.order_by("id")
        context["filas_demanda_insatisfecha"] = (
            self.object.filas_demanda_insatisfecha.order_by("id")
        )
        context["filas_articulacion"] = self.object.filas_articulacion.order_by("id")
        context["horarios_funcionamiento"] = (
            self.object.horarios_funcionamiento.order_by("id")
        )
        context["totales_salas"] = self._sum_numeric_rows(
            context["filas_salas"],
            [
                "cantidad_salas",
                "superficie_exclusiva_m2",
                "cantidad_ninos",
                "cantidad_personal_sala",
            ],
        )
        context["total_demanda_insatisfecha"] = sum(
            item.cantidad_demanda_insatisfecha or 0
            for item in context["filas_demanda_insatisfecha"]
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
        for section in SECCIONES_FORMULARIO_CDI:
            items = []
            for field_name in section["fields"]:
                items.append(
                    {
                        "label": _obtener_etiquetas_campos_formulario().get(
                            field_name, ETIQUETAS_CAMPOS.get(field_name, field_name)
                        ),
                        "value": _mostrar_valor_campo(formulario, field_name),
                    }
                )
            sections.append({"title": section["title"], "items": items})
        return sections


class FormularioCDIEditBaseView(LoginRequiredMixin, View):
    template_name = "centrodeinfancia/formulario_cdi_form.html"
    form_class = FormularioCDIForm

    def get_centro(self):
        return _obtener_centro_filtrado_o_404(self.request.user, self.kwargs["pk"])

    def get_form_instance(self):
        return getattr(self, "_form_instance", None)

    def get_initial(self):
        centro = self.get_centro()
        initial = {
            "nombre_cdi": centro.nombre,
            "codigo_cdi": centro.codigo_cdi,
            "ambito": centro.ambito,
            "provincia_cdi": centro.provincia,
            "departamento_cdi": centro.departamento,
            "municipio_cdi": centro.municipio,
            "localidad_cdi": centro.localidad,
            "calle_cdi": centro.calle,
            "numero_puerta_cdi": centro.numero,
            "codigo_postal_cdi": centro.codigo_postal,
            "latitud_geografica_cdi": centro.latitud,
            "longitud_geografica_cdi": centro.longitud,
            "telefono_cdi": centro.telefono,
            "email_cdi": centro.mail,
            "nombre_referente_cdi": centro.nombre_referente,
            "apellido_referente_cdi": centro.apellido_referente,
            "telefono_referente_cdi": centro.telefono_referente,
            "email_referente_cdi": centro.email_referente,
            "meses_funcionamiento": centro.meses_funcionamiento,
            "dias_funcionamiento": centro.dias_funcionamiento,
            "tipo_jornada": centro.tipo_jornada,
            "tipo_jornada_otra": centro.tipo_jornada_otra,
            "oferta_servicios": centro.oferta_servicios,
            "modalidad_gestion": centro.modalidad_gestion,
            "modalidad_gestion_otra": centro.modalidad_gestion_otra,
            "nombre_organizacion_gestora": centro.organizacion,
            "cuit_organizacion_gestora": centro.cuit_organizacion_gestiona,
        }
        for horario in centro.horarios_funcionamiento.all():
            initial[f"horario_{horario.dia}_apertura"] = horario.hora_apertura
            initial[f"horario_{horario.dia}_cierre"] = horario.hora_cierre
        return initial

    def construir_formulario(self, data=None, instance=None):
        initial = None
        if not instance or not instance.pk:
            initial = self.get_initial()
        return self.form_class(data=data, instance=instance, initial=initial)

    def construir_formsets(self, data=None, instance=None):
        if instance and instance.pk:
            self.ensure_fixed_rows(instance)

        clase_formset_distribucion_salas = construir_clase_formset_distribucion_salas(
            0 if instance and instance.pk else len(OPCIONES_GRUPO_ETARIO_SALAS)
        )
        clase_formset_demanda_insatisfecha = (
            construir_clase_formset_demanda_insatisfecha(
                0 if instance and instance.pk else len(OPCIONES_GRUPO_ETARIO_DEMANDA)
            )
        )
        clase_formset_articulacion = construir_clase_formset_articulacion(
            0 if instance and instance.pk else len(OPCIONES_INSTITUCIONES_ARTICULACION)
        )

        filas_iniciales_salas = (
            []
            if instance
            else construir_filas_iniciales_fijas(
                OPCIONES_GRUPO_ETARIO_SALAS, "grupo_etario"
            )
        )
        filas_iniciales_demanda = (
            []
            if instance
            else construir_filas_iniciales_fijas(
                OPCIONES_GRUPO_ETARIO_DEMANDA, "grupo_etario"
            )
        )
        filas_iniciales_articulacion = (
            []
            if instance
            else construir_filas_iniciales_fijas(
                OPCIONES_INSTITUCIONES_ARTICULACION, "tipo_institucion"
            )
        )
        formsets = {
            "formset_distribucion_salas": clase_formset_distribucion_salas(
                data=data,
                instance=instance or FormularioCDI(),
                prefix="distribucion_salas",
                initial=filas_iniciales_salas,
            ),
            "formset_demanda_insatisfecha": clase_formset_demanda_insatisfecha(
                data=data,
                instance=instance or FormularioCDI(),
                prefix="demanda_insatisfecha_por_grupo_etario",
                initial=filas_iniciales_demanda,
            ),
            "formset_articulacion": clase_formset_articulacion(
                data=data,
                instance=instance or FormularioCDI(),
                prefix="frecuencia_articulacion",
                initial=filas_iniciales_articulacion,
            ),
        }
        return formsets

    @staticmethod
    def construir_secciones_formulario(form):
        sections = []
        for section in form.definiciones_secciones:
            rows = []
            field_names = section["fields"]
            forced_row_starts = set(FILAS_FORZADAS)
            index = 0

            while index < len(field_names):
                current_name = field_names[index]
                forced_row = FILAS_FORZADAS.get(current_name)

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

                if current_name in CAMPOS_ANCHO_COMPLETO:
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
                    and next_name not in CAMPOS_ANCHO_COMPLETO
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
            "section_fields": self.construir_secciones_formulario(form),
            "horario_fields": [
                {
                    "dia": dia,
                    "etiqueta": etiqueta,
                    "apertura": form[f"horario_{dia}_apertura"],
                    "cierre": form[f"horario_{dia}_cierre"],
                }
                for dia, etiqueta in form.DIAS_SEMANA
            ],
            "formset_distribucion_salas": formsets["formset_distribucion_salas"],
            "formset_demanda_insatisfecha": formsets["formset_demanda_insatisfecha"],
            "formset_articulacion": formsets["formset_articulacion"],
            "is_edit": bool(instance and instance.pk),
        }

    @staticmethod
    def ensure_fixed_rows(formulario):
        room_existing = set(
            formulario.filas_distribucion_salas.values_list("grupo_etario", flat=True)
        )
        waitlist_existing = set(
            formulario.filas_demanda_insatisfecha.values_list("grupo_etario", flat=True)
        )
        articulation_existing = set(
            formulario.filas_articulacion.values_list("tipo_institucion", flat=True)
        )

        for value, _label in OPCIONES_GRUPO_ETARIO_SALAS:
            if value not in room_existing:
                FormularioCDIRoomDistribution.objects.create(
                    formulario=formulario,
                    grupo_etario=value,
                )

        for value, _label in OPCIONES_GRUPO_ETARIO_DEMANDA:
            if value not in waitlist_existing:
                FormularioCDIWaitlistByAgeGroup.objects.create(
                    formulario=formulario,
                    grupo_etario=value,
                )

        for value, _label in OPCIONES_INSTITUCIONES_ARTICULACION:
            if value not in articulation_existing:
                FormularioCDIArticulationFrequency.objects.create(
                    formulario=formulario,
                    tipo_institucion=value,
                )

    def get(self, request, *args, **kwargs):
        instance = self.get_form_instance()
        form = self.construir_formulario(instance=instance)
        formsets = self.construir_formsets(instance=instance)
        return render(
            request, self.template_name, self.get_context(form, formsets, instance)
        )

    def post(self, request, *args, **kwargs):
        instance = self.get_form_instance()
        form = self.construir_formulario(data=request.POST, instance=instance)
        formsets = self.construir_formsets(data=request.POST, instance=instance)

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
        if not hasattr(self, "_form_instance"):
            self._form_instance = _obtener_formulario_filtrado_o_404(
                self.request.user,
                self.kwargs["pk"],
                self.kwargs["form_pk"],
            )
        return self._form_instance

    def get_success_message(self, formulario):
        return f"Formulario #{formulario.pk} actualizado correctamente."
