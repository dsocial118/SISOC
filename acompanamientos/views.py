from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.views.decorators.http import require_POST
from django.db.models import Q
from admisiones.models.admisiones import (
    Admision,
    InformeTecnico,
    DocumentosExpediente,
)
from acompanamientos.acompanamiento_service import AcompanamientoService
from acompanamientos.models.hitos import Hitos
from comedores.models import Comedor


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


# TODO: Sincronizar con la tarea de Pablo
class AcompanamientoDetailView(DetailView):
    model = Comedor
    template_name = "acompañamiento_detail.html"
    context_object_name = "comedor"
    pk_url_kwarg = "comedor_id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor = self.object

        # Optimización: Cache de grupos del usuario
        user_groups = list(self.request.user.groups.values_list("name", flat=True))
        context["es_tecnico_comedor"] = (
            self.request.user.is_superuser or "Tecnico Comedor" in user_groups
        )

        context["hitos"] = AcompanamientoService.obtener_hitos(comedor)

        # Optimización: Query única con select_related para evitar múltiples queries
        admision = (
            Admision.objects.select_related("comedor")
            .filter(comedor=comedor)
            .exclude(num_if__isnull=True)
            .exclude(num_if="")
            .order_by("-id")
            .first()
        )
        context["admision"] = admision

        info_relevante = None
        resolucion = None
        doc_resolucion = None

        if admision:
            # Optimización: Usar la admision ya obtenida en lugar de filtrar por comedor
            info_relevante = (
                InformeTecnico.objects.filter(admision=admision).order_by("-id").first()
            )
            doc_resolucion = (
                DocumentosExpediente.objects.filter(
                    admision=admision, tipo="Resolución"
                )
                .order_by("-creado")
                .first()
            )
        if doc_resolucion:
            resolucion = doc_resolucion.value or doc_resolucion.nombre

        # Asignar valores al contexto
        context["info_relevante"] = info_relevante
        context["numero_if"] = admision.num_if if admision else None
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
