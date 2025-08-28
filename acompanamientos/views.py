from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.views.decorators.http import require_POST

from acompanamientos.acompanamiento_service import AcompanamientoService
from acompanamientos.models.hitos import Hitos
from comedores.models import Comedor


@require_POST
def restaurar_hito(request, comedor_id):
    campo = request.POST.get("campo")
    hito = get_object_or_404(Hitos, comedor_id=comedor_id)

    # Verifica si el campo existe en el modelo
    if hasattr(hito, campo) and campo not in ["id", "comedor", "fecha"]:
        setattr(hito, campo, False)  # Cambia el valor del campo a False (0)
        hito.save()
        messages.success(
            request, f"El campo '{campo}' ha sido restaurado correctamente."
        )
    else:
        messages.error(request, f"El campo '{campo}' no existe en el modelo Hitos.")

    # Redirige a la página anterior
    return redirect(request.META.get("HTTP_REFERER", "/"))


class AcompanamientoDetailView(DetailView):
    model = Comedor
    template_name = "acompañamiento_detail.html"
    context_object_name = "comedor"
    pk_url_kwarg = "comedor_id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor = self.object

        user_groups = list(self.request.user.groups.values_list("name", flat=True))
        context["es_tecnico_comedor"] = (
            self.request.user.is_superuser or "Tecnico Comedor" in user_groups
        )

        context["hitos"] = AcompanamientoService.obtener_hitos(comedor)
        context["fechas_hitos"] = AcompanamientoService.obtener_fechas_hitos(comedor)

        datos_admision = AcompanamientoService.obtener_datos_admision(comedor)

        admision = datos_admision.get("admision")
        info_relevante = datos_admision.get("info_relevante")
        anexo = datos_admision.get("anexo")

        context["admision"] = admision
        context["info_relevante"] = info_relevante
        context["numero_if"] = datos_admision.get("numero_if")
        context["numero_disposicion"] = datos_admision.get("numero_disposicion")

        prestaciones_detalle = AcompanamientoService.obtener_prestaciones_detalladas(
            anexo
        )

        context["prestaciones_por_dia"] = prestaciones_detalle.get(
            "prestaciones_por_dia", []
        )
        context["prestaciones_dias"] = prestaciones_detalle.get("prestaciones_dias", [])
        context["dias_semana"] = prestaciones_detalle.get("dias_semana", [])

        return context


class ComedoresAcompanamientoListView(ListView):
    model = Comedor
    template_name = "lista_comedores.html"
    context_object_name = "comedores"
    paginate_by = 10  # Cantidad de resultados por página

    def get_queryset(self):
        user = self.request.user
        busqueda = self.request.GET.get("busqueda", "").strip().lower()

        return AcompanamientoService.obtener_comedores_acompanamiento(user, busqueda)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("busqueda", "")
        return context
