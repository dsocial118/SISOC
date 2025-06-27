from django.shortcuts import redirect
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from centrodefamilia.models import ParticipanteActividad
from centrodefamilia.forms import ParticipanteActividadForm
from ciudadanos.models import (
    Ciudadano,
    Archivo, CiudadanoPrograma, Derivacion,
    DimensionEconomia, DimensionEducacion, DimensionFamilia,
    DimensionSalud, DimensionTrabajo, DimensionVivienda,
    GrupoFamiliar, GrupoHogar, HistorialAlerta,
    HistorialCiudadanoProgramas, Intervencion, Llamado
)
from django.db.models import CharField
from django.db.models.functions import Cast


class ParticipanteActividadCreateView(CreateView):
    model = ParticipanteActividad
    form_class = ParticipanteActividadForm
    template_name = "centros/participanteactividad_form.html"

    def get_initial(self):
        initial = super().get_initial()
        actividad_id = self.kwargs.get("actividad_id")
        if actividad_id:
            initial["actividad_centro"] = actividad_id
        return initial

    def form_valid(self, form):
        return super().form_valid(form)

    def get_success_url(self):
        centro_id = self.kwargs.get("centro_id")
        actividad_id = self.kwargs.get("actividad_id")
        return reverse_lazy(
            "actividadcentro_detail",
            kwargs={"centro_id": centro_id, "pk": actividad_id},
        )

    def post(self, request, *args, **kwargs):
        actividad_id = self.kwargs.get("actividad_id")

        if "documento" in request.POST and "nombre" in request.POST:
            try:
                ciudadano = Ciudadano.objects.get(documento=request.POST.get("documento"))
                ParticipanteActividad.objects.create(
                    actividad_centro_id=actividad_id,
                    ciudadano=ciudadano
                )
                messages.success(self.request, "Participante agregado desde búsqueda.")
                return redirect(self.get_success_url())
            except Ciudadano.DoesNotExist:
                messages.error(self.request, "Ciudadano no encontrado.")

        form = self.get_form()
        if form.is_valid():
            ciudadano = Ciudadano.objects.create(
                nombre=form.cleaned_data["nombre"],
                apellido=form.cleaned_data["apellido"],
                documento=form.cleaned_data["dni"],
                fecha_nacimiento=form.cleaned_data["fecha_nacimiento"],
                tipo_documento=form.cleaned_data.get("tipo_documento"),
                sexo=form.cleaned_data.get("genero"),
            )

            # Crear todas las relaciones obligatorias
            DimensionEconomia.objects.create(ciudadano=ciudadano)
            DimensionEducacion.objects.create(ciudadano=ciudadano)
            DimensionFamilia.objects.create(ciudadano=ciudadano)
            DimensionSalud.objects.create(ciudadano=ciudadano)
            DimensionTrabajo.objects.create(ciudadano=ciudadano)
            DimensionVivienda.objects.create(ciudadano=ciudadano)
            ParticipanteActividad.objects.create(
                actividad_centro_id=actividad_id,
                ciudadano=ciudadano
            )

            messages.success(request, "Ciudadano y Participante creados correctamente.")
            return redirect(self.get_success_url())

        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("query", "")
        if len(query) >= 4:
            ciudadanos = Ciudadano.objects.annotate(
                doc_str=Cast("documento", CharField())
            ).filter(doc_str__startswith=query)[:10]
            context["ciudadanos"] = ciudadanos
            context["no_resultados"] = not ciudadanos.exists()
        context["centro_id"] = self.kwargs.get("centro_id")
        context["actividad_id"] = self.kwargs.get("actividad_id")
        return context
