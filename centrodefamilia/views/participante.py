# centrodefamilia/views/participante.py

import threading
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, View, ListView

from centrodefamilia.models import ParticipanteActividad, ActividadCentro
from centrodefamilia.forms import ParticipanteActividadForm
from centrodefamilia.services.participante import (
    ParticipanteService,
    AlreadyRegistered,
    CupoExcedido,
    SexoNoPermitido,
)


class ParticipanteActividadCreateView(LoginRequiredMixin, CreateView):
    model = ParticipanteActividad
    form_class = ParticipanteActividadForm
    template_name = "centros/participanteactividad_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["actividad_id"] = self.kwargs.get("actividad_id")
        kwargs["usuario"] = self.request.user
        return kwargs

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
        allow_waitlist = request.POST.get("allow_waitlist") == "1"
        form = self.get_form()

        if not ciudadano_id and not form.is_valid():
            return self.form_invalid(form)

        try:
            tipo, participante = ParticipanteService.procesar_creacion(
                usuario=request.user,
                actividad_id=actividad_id,
                ciudadano_id=ciudadano_id,
                datos=form.cleaned_data if not ciudadano_id else None,
                allow_waitlist=allow_waitlist,
            )
            if tipo == "inscrito":
                messages.success(request, "Participante agregado correctamente.")
            else:
                messages.success(request, "Participante agregado a la lista de espera.")
            return redirect(self.get_success_url())

        except AlreadyRegistered as e:
            messages.warning(request, str(e))
            return redirect(self.get_success_url())
        except SexoNoPermitido as e:
            messages.warning(request, str(e))
            return redirect(self.get_success_url())
        except CupoExcedido as e:
            # Cupo completo: inscribir automáticamente en lista de espera
            tipo2, participante2 = ParticipanteService.procesar_creacion(
                usuario=request.user,
                actividad_id=actividad_id,
                ciudadano_id=ciudadano_id,
                datos=form.cleaned_data if not ciudadano_id else None,
                allow_waitlist=True,
            )
            messages.success(
                request, "Cupo completo: participante agregado a lista de espera."
            )
            return redirect(self.get_success_url())
        except (LookupError, ValueError) as e:
            messages.error(request, str(e))
            return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        self.object = None
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("query") or ""
        context["ciudadanos"] = ParticipanteService.buscar_ciudadanos_por_documento(
            query
        )
        context["no_resultados"] = not bool(context["ciudadanos"])
        context["centro_id"] = self.kwargs.get("centro_id")
        context["actividad_id"] = self.kwargs.get("actividad_id")
        return context


# centrodefamilia/views/participante.py


class ParticipanteActividadDeleteView(LoginRequiredMixin, View):
    template_name = "centros/participanteactividad_confirm_delete.html"

    def get(self, request, *args, **kwargs):
        participante = get_object_or_404(ParticipanteActividad, pk=kwargs["pk"])
        return render(
            request,
            self.template_name,
            {
                "participante": participante,
                "centro_id": kwargs["centro_id"],
                "actividad_id": kwargs["actividad_id"],
            },
        )

    def post(self, request, *args, **kwargs):
        participante_id = kwargs["pk"]
        participante = get_object_or_404(ParticipanteActividad, pk=participante_id)
        try:
            ParticipanteService.dar_de_baja(participante_id, request.user)
            messages.success(request, "Participante dado de baja correctamente.")
        except Exception as e:
            messages.error(request, str(e))
        return redirect(
            reverse_lazy(
                "actividadcentro_detail",
                kwargs={
                    "centro_id": kwargs["centro_id"],
                    "pk": kwargs["actividad_id"],
                },
            )
        )


class ParticipanteActividadListEsperaView(LoginRequiredMixin, ListView):
    model = ParticipanteActividad
    template_name = "centros/participanteactividad_lista_espera.html"
    context_object_name = "participantes"

    def get_queryset(self):
        actividad_id = self.kwargs.get("actividad_id")
        return ParticipanteActividad.objects.filter(
            actividad_centro_id=actividad_id, estado="lista_espera"
        ).select_related("ciudadano")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["centro_id"] = self.kwargs.get("centro_id")
        context["actividad_id"] = self.kwargs.get("actividad_id")
        return context


class ParticipanteActividadPromoverView(LoginRequiredMixin, View):
    """
    Promueve un participante de lista de espera a inscrito,
    o maneja GET redirigiendo con error de cupo.
    """

    def get(self, request, *args, **kwargs):
        # Si alguien accede por GET, reenviamos al detalle con promo_error
        centro_id = kwargs.get("centro_id")
        actividad_id = kwargs.get("actividad_id")
        detail_url = reverse_lazy(
            "actividadcentro_detail",
            kwargs={"centro_id": centro_id, "pk": actividad_id},
        )
        return redirect(f"{detail_url}?promo_error=1")

    def post(self, request, *args, **kwargs):
        participante = get_object_or_404(ParticipanteActividad, pk=kwargs["pk"])
        actividad = participante.actividad_centro
        centro_id = kwargs["centro_id"]
        actividad_id = kwargs["actividad_id"]
        detail_url = reverse_lazy(
            "actividadcentro_detail",
            kwargs={"centro_id": centro_id, "pk": actividad_id},
        )

        # Verifico cupo antes de promover
        inscritos = ParticipanteService.contar_inscritos(actividad)
        if inscritos >= actividad.cantidad_personas:
            # No hay espacio: redirijo con el flag para el modal
            return redirect(f"{detail_url}?promo_error=1")

        # Hay cupo: promover al siguiente de la lista
        siguiente = ParticipanteService.promover_lista_espera(actividad, request.user)
        if siguiente:
            messages.success(
                request, "Participante promovido a inscrito correctamente."
            )
        else:
            messages.info(request, "No hay participantes en lista de espera.")
        return redirect(detail_url)
