from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.views.decorators.http import require_POST
from django.db.models import Q
from admisiones.models.admisiones import (
    Admision,
    InformeTecnicoBase,
    DocumentosExpediente,
)
from acompanamientos.acompanamiento_service import AcompanamientoService
from acompanamientos.models.hitos import Hitos
from comedores.models.comedor import Comedor

@require_POST
def restaurar_hito(request, comedor_id):
    campo = request.POST.get("campo")
    hito = get_object_or_404(Hitos, comedor_id=comedor_id)

    # Verifica si el campo existe en el modelo
    if hasattr(hito, campo):
        setattr(hito, campo, False)  # Cambia el valor del campo a False (0)
        hito.save()
        messages.success(
            request, f"El campo '{campo}' ha sido restaurado correctamente."
        )
    else:
        messages.error(request, f"El campo '{campo}' no existe en el modelo Hitos.")

    # Redirige a la página anterior
    return redirect(request.META.get("HTTP_REFERER", "/"))



# TODO: Sincronizar con la tarea de Pablo y migrar a clases
class AcompanamientoDetailView(DetailView):
    model = Comedor
    template_name = "acompañamiento_detail.html"
    context_object_name = "comedor"
    pk_url_kwarg = "comedor_id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor = self.object
        context["hitos"] = AcompanamientoService.obtener_hitos(comedor)

        admision = (
            Admision.objects.filter(comedor=comedor)
            .exclude(num_if__isnull=True)
            .exclude(num_if="")
            .order_by("-id")
            .first()
        )
        context["admision"] = admision

        info_relevante = None
        if admision:
            info_relevante = (
                InformeTecnicoBase.objects.filter(admision__comedor=comedor)
                .order_by("-id")
                .first()
            )
        context["info_relevante"] = info_relevante

        context["numero_if"] = admision.num_if if admision else None

        resolucion = None
        if admision:
            doc_resolucion = (
                DocumentosExpediente.objects.filter(
                    admision__comedor=comedor, tipo="Resolución"
                )
                .order_by("-creado")
                .first()
            )
            if doc_resolucion:
                resolucion = doc_resolucion.value or doc_resolucion.nombre

        context["numero_resolucion"] = resolucion

        # Prestaciones
        if info_relevante:
            context["prestaciones_dias"] = [
                {"tipo": "Desayuno", "cantidad": info_relevante.prestaciones_desayuno},
                {"tipo": "Almuerzo", "cantidad": info_relevante.prestaciones_almuerzo},
                {"tipo": "Merienda", "cantidad": info_relevante.prestaciones_merienda},
                {"tipo": "Cena", "cantidad": info_relevante.prestaciones_cena},
            ]
        else:
            context["prestaciones_dias"] = []

        return context

class ComedoresAcompanamientoListView(ListView):
    model = Admision
    template_name = "lista_comedores.html"
    context_object_name = "admisiones"

    def get_queryset(self):
        user = self.request.user
        # TODO: Sincronizar estado con la tarea de Pablo

        if user.is_superuser:
            return (
                # TODO: El estado se cambia cuando se termina la ultima etapa de admision que esta trabajando Pablo.
                Admision.objects.filter(estado__nombre="Finalizada")
                .values(
                    "comedor__id",
                    "comedor__nombre",
                )
                .distinct()
            )
        else:
            return (
                Admision.objects.filter(
                    Q(estado__nombre="Test")
                    & (
                        Q(comedor__dupla__abogado=user)
                        | Q(comedor__dupla__tecnico=user)
                    )
                )
                .values(
                    "comedor__id",
                    "comedor__nombre",
                )
                .distinct()
            )
