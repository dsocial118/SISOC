# centrodefamilia/views/participante.py

from django.shortcuts import redirect
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from centrodefamilia.models import ParticipanteActividad
from centrodefamilia.forms import ParticipanteActividadForm
from centrodefamilia.services.participante_service import ParticipanteService
from ciudadanos.models import (
    Ciudadano,
    CiudadanoPrograma,
    Programa,
    HistorialCiudadanoProgramas,
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
        centro_id = self.kwargs.get("centro_id")
        actividad_id = self.kwargs.get("actividad_id")
        return reverse_lazy(
            "actividadcentro_detail",
            kwargs={"centro_id": centro_id, "pk": actividad_id},
        )

    def post(self, request, *args, **kwargs):
        self.object = None
        actividad_id = self.kwargs.get("actividad_id")
        user = request.user

        # 1) Participante existente
        ciudadano_id = request.POST.get("ciudadano_id")
        if ciudadano_id:
            try:
                ciudadano = Ciudadano.objects.get(pk=ciudadano_id)
            except Ciudadano.DoesNotExist:
                messages.error(request, "Ciudadano no encontrado.")
                return redirect(self.get_success_url())

            # 1.a) Asociar a la actividad
            ParticipanteService.crear_participante(actividad_id, ciudadano)

            # 1.b) Crear o recuperar vínculo en CiudadanoPrograma (programa=1)
            cp, created = CiudadanoPrograma.objects.get_or_create(
                ciudadano=ciudadano,
                programas_id=1,
                defaults={"creado_por": user}
            )
            # 1.c) Si se crea nuevo, registrar en historial
            if created:
                HistorialCiudadanoProgramas.objects.create(
                    programa_id=1,
                    ciudadano=ciudadano,
                    accion="agregado",
                    usuario=user
                )

            messages.success(request, "Participante existente agregado correctamente.")
            return redirect(self.get_success_url())

        # 2) Nuevo ciudadano + dimensiones
        form = self.get_form()
        if form.is_valid():
            nuevo_ciudadano = ParticipanteService.crear_ciudadano_con_dimensiones(
                form.cleaned_data
            )
            # 2.a) Asociación a la actividad
            ParticipanteService.crear_participante(actividad_id, nuevo_ciudadano)
            # 2.b) Crear vínculo Ciudadano–Programa
            CiudadanoPrograma.objects.create(
                ciudadano=nuevo_ciudadano,
                programas_id=1,
                creado_por=user
            )
            # 2.c) Registrar en historial
            HistorialCiudadanoProgramas.objects.create(
                programa_id=1,
                ciudadano=nuevo_ciudadano,
                accion="agregado",
                usuario=user
            )

            messages.success(request, "Ciudadano y participante creados correctamente.")
            return redirect(self.get_success_url())

        return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("query", "")
        if len(query) >= 4:
            from django.db.models import CharField
            from django.db.models.functions import Cast

            context["ciudadanos"] = (
                Ciudadano.objects
                .annotate(doc_str=Cast("documento", CharField()))
                .filter(doc_str__startswith=query)[:10]
            )
            context["no_resultados"] = not context["ciudadanos"].exists()

        context["centro_id"] = self.kwargs.get("centro_id")
        context["actividad_id"] = self.kwargs.get("actividad_id")
        return context
