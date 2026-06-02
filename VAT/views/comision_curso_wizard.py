"""Wizard de 3 pasos para crear una Comisión de Curso.

Paso 1 - Información básica (ubicación, cupo, estado, fechas, observaciones).
Paso 2 - Horarios (formset de ComisionHorario).
Paso 3 - Confirmación + persistencia transaccional.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from formtools.wizard.views import SessionWizardView

from VAT.forms import (
    ComisionCursoWizardStep1Form,
    ComisionCursoWizardStep2FormSet,
    ComisionCursoWizardStep3Form,
)
from VAT.models import (
    ComisionCurso,
    ComisionHorario,
    Curso,
)
from VAT.services.access_scope import can_user_edit_centro


WIZARD_FORMS = [
    ("info", ComisionCursoWizardStep1Form),
    ("horarios", ComisionCursoWizardStep2FormSet),
    ("confirmacion", ComisionCursoWizardStep3Form),
]

WIZARD_STEP_TEMPLATES = {
    "info": "vat/comision_curso_wizard/step1_info.html",
    "horarios": "vat/comision_curso_wizard/step2_horarios.html",
    "confirmacion": "vat/comision_curso_wizard/step3_confirmacion.html",
}


class ComisionCursoWizardView(LoginRequiredMixin, SessionWizardView):
    form_list = WIZARD_FORMS

    def dispatch(self, request, *args, **kwargs):
        curso_id = kwargs.get("curso_id")
        if not curso_id:
            raise PermissionDenied("Falta el parámetro curso.")
        self.curso = get_object_or_404(
            Curso.objects.select_related("centro", "plan_estudio"),
            pk=curso_id,
        )
        if not can_user_edit_centro(request.user, self.curso.centro):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        return [WIZARD_STEP_TEMPLATES[self.steps.current]]

    def get(self, request, *args, **kwargs):
        # Always start a fresh wizard when opening the URL directly.
        # This avoids showing stale horarios rows from an abandoned session.
        self.storage.reset()
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)
        if step == "info":
            kwargs["curso"] = self.curso
        return kwargs

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        context["curso"] = self.curso
        context["centro"] = self.curso.centro
        context["wizard_cancel_url"] = self._centro_cursos_url()
        context["wizard_back_url"] = self._centro_cursos_url()
        step1_data = self.get_cleaned_data_for_step("info") or {}
        step2_data = self.get_cleaned_data_for_step("horarios") or []
        context["step1_data"] = step1_data
        context["step2_data"] = step2_data
        context["estado_label"] = self._estado_label(step1_data)

        if self.steps.current == "confirmacion":
            context["horarios_resumen"] = self._build_horarios_resumen(step2_data)
            context["horarios_total_label"] = self._format_total_semanal(step2_data)
        return context

    @staticmethod
    def _minutos(hora):
        return hora.hour * 60 + hora.minute if hora else 0

    def _build_horarios_resumen(self, step2_data):
        filas = []
        for horario in step2_data:
            if not horario or horario.get("DELETE"):
                continue
            inicio = horario.get("hora_desde")
            fin = horario.get("hora_hasta")
            duracion_min = self._minutos(fin) - self._minutos(inicio)
            horas = duracion_min // 60
            minutos = duracion_min % 60
            filas.append(
                {
                    "dia": horario.get("dia_semana"),
                    "hora_desde": inicio,
                    "hora_hasta": fin,
                    "duracion": f"{horas} hs {minutos} minutos",
                    "estado_label": (
                        "Activo" if horario.get("vigente") == "1" else "Inactivo"
                    ),
                }
            )
        return filas

    def _format_total_semanal(self, step2_data):
        total = 0
        for horario in step2_data:
            if not horario or horario.get("DELETE"):
                continue
            total += self._minutos(horario.get("hora_hasta")) - self._minutos(
                horario.get("hora_desde")
            )
        horas = total // 60
        minutos = total % 60
        return f"{horas} hs {minutos} minutos"

    def _estado_label(self, step1_data):
        estado = (step1_data or {}).get("estado") or "planificada"
        return dict(ComisionCurso.ESTADO_COMISION_CURSO_CHOICES).get(
            estado, "Planificada"
        )

    def _centro_cursos_url(self):
        base = reverse("vat_centro_detail", kwargs={"pk": self.curso.centro_id})
        return f"{base}#cursos"

    # Django form wizard passes form_dict for named forms in this flow.
    def done(self, form_list, form_dict, **kwargs):  # pylint: disable=arguments-differ
        info = form_dict["info"].cleaned_data
        horarios_formset = form_dict["horarios"]

        with transaction.atomic():
            comision = ComisionCurso.objects.create(
                curso=self.curso,
                ubicacion=info["ubicacion"],
                cupo_total=info["cupo_total"],
                estado=info["estado"],
                fecha_inicio=info["fecha_inicio"],
                fecha_fin=info["fecha_fin"],
                observaciones=info.get("observaciones") or "",
            )
            for horario_form in horarios_formset.forms:
                data = horario_form.cleaned_data
                if not data or data.get("DELETE"):
                    continue
                ComisionHorario.objects.create(
                    comision_curso=comision,
                    dia_semana=data["dia_semana"],
                    hora_desde=data["hora_desde"],
                    hora_hasta=data["hora_hasta"],
                    vigente=data["vigente"] == "1",
                )

        messages.success(
            self.request,
            f"Comisión creada con {comision.horarios.count()} horario(s).",
        )
        base = reverse("vat_centro_detail", kwargs={"pk": self.curso.centro_id})
        return redirect(f"{base}?refresh=1#cursos")
