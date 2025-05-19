from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.generic import ListView, DetailView
from acompanamientos.models.acompanamiento import InformacionRelevante, Prestacion
from acompanamientos.models.hitos import Hitos
from admisiones.models.admisiones import Admision
from comedores.models.comedor import Comedor
from comedores.models.relevamiento import Relevamiento
from acompanamientos.acompanamiento_service import AcompanamientoService
from django.db.models import Q


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
        context["info_relevante"] = InformacionRelevante.objects.filter(comedor=comedor).first()
        relevamiento = (
            Relevamiento.objects.filter(comedor=comedor).order_by("-fecha_visita").first()
        )
        prestacion = (
            relevamiento.prestacion if relevamiento and relevamiento.prestacion else None
        )
        dias = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]

        prestaciones_dias = []
        if prestacion:
            for dia in dias:
                prestaciones_dias.append(
                    {
                        "dia": dia,
                        "desayuno": getattr(prestacion, f"{dia}_desayuno_actual", "-"),
                        "almuerzo": getattr(prestacion, f"{dia}_almuerzo_actual", "-"),
                        "merienda": getattr(prestacion, f"{dia}_merienda_actual", "-"),
                        "cena": getattr(prestacion, f"{dia}_cena_actual", "-"),
                    }
                )
        context["prestaciones_dias"] = prestaciones_dias
        return context


def restaurar_hito(request, comedor_id):
    if request.method == "POST":
        campo = request.POST.get("campo")
        hito = get_object_or_404(Hitos, comedor_id=comedor_id)

        # Verifica si el campo existe en el modelo
        if hasattr(hito, campo):
            setattr(hito, campo, False)  # Cambia el valor del campo a False (0)
            hito.save()
            return JsonResponse({"success": True, "message": f"El campo '{campo}' ha sido restaurado."})
        else:
            return JsonResponse({"success": False, "message": f"El campo '{campo}' no existe."}, status=400)

    return JsonResponse({"success": False, "message": "Método no permitido."}, status=405)


class ComedoresAcompanamientoListView(ListView):
    model = Admision
    template_name = "lista_comedores.html"
    context_object_name = "admisiones"

    def get_queryset(self):
        user = self.request.user
        # TODO: Sincronizar estado con la tarea de Pablo

        if user.is_superuser:
            return (
                Admision.objects.filter(estado__nombre="Test")
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
