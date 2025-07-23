# centrodefamilia/views/participante.py
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, DeleteView

from centrodefamilia.models import ParticipanteActividad
from centrodefamilia.forms import ParticipanteActividadForm
from centrodefamilia.services.participante import (
    AlreadyRegistered,
    CupoExcedido,
    ParticipanteService,
    SexoNoPermitido,
)


class ParticipanteActividadCreateView(LoginRequiredMixin, CreateView):
    model = ParticipanteActividad
    form_class = ParticipanteActividadForm
    template_name = "centros/participanteactividad_form.html"

    def get_initial(self):
        initial = super().get_initial()
        actividad_id = self.kwargs.get("actividad_id")
        if actividad_id:
            initial["actividad_centro"] = actividad_id
        return initial

    def get_success_url(self):
        return reverse_lazy(
            "actividadcentro_detail",
            kwargs={
                "centro_id": self.kwargs.get("centro_id"),
                "pk": self.kwargs.get("actividad_id"),
            },
        )

    def post(self, request, *args, **kwargs):
        actividad_id = self.kwargs.get("actividad_id")
        ciudadano_id = request.POST.get("ciudadano_id")
        form = self.get_form()

        # Si no es un agregado existente y el form no es válido, mostrar errores
        if not ciudadano_id and not form.is_valid():
            return self.form_invalid(form)

        try:
            tipo, _ = ParticipanteService.procesar_creacion(
                usuario=request.user,
                actividad_id=actividad_id,
                ciudadano_id=ciudadano_id,
                datos=form.cleaned_data if not ciudadano_id else None,
            )

            if tipo == "existente":
                messages.success(
                    request, "Participante existente agregado correctamente."
                )
            else:
                messages.success(
                    request, "Ciudadano y participante creados correctamente."
                )

        except AlreadyRegistered as e:
            messages.warning(request, str(e))
        except CupoExcedido as e:
            messages.warning(request, str(e))
        except SexoNoPermitido as e:
            messages.warning(request, str(e))
        except (LookupError, ValueError) as e:
            messages.error(request, str(e))
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("query") or ""
        context["ciudadanos"] = ParticipanteService.buscar_ciudadanos(query)
        context["no_resultados"] = not bool(context["ciudadanos"])
        context["centro_id"] = self.kwargs.get("centro_id")
        context["actividad_id"] = self.kwargs.get("actividad_id")
        return context


class ParticipanteActividadDeleteView(LoginRequiredMixin, DeleteView):
    model = ParticipanteActividad
    template_name = "centros/participanteactividad_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy(
            "actividadcentro_detail",
            kwargs={
                "centro_id": self.kwargs.get("centro_id"),
                "pk": self.kwargs.get("actividad_id"),
            },
        )

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Participante eliminado correctamente.")
        return super().delete(request, *args, **kwargs)
