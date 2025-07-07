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

    if hasattr(hito, campo):
        setattr(hito, campo, False)
        hito.save()
        messages.success(
            request, f"El campo '{campo}' ha sido restaurado correctamente."
        )
    else:
        messages.error(request, f"El campo '{campo}' no existe en el modelo Hitos.")

    return redirect(request.META.get("HTTP_REFERER", "/"))


class AcompanamientoDetailView(DetailView):
    model = Comedor
    template_name = "acompañamiento_detail.html"
    context_object_name = "comedor"
    pk_url_kwarg = "comedor_id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor = self.object

        context["hitos"] = AcompanamientoService.obtener_hitos(comedor)
        context["es_tecnico_comedor"] = (
            AcompanamientoService.verificar_permisos_tecnico_comedor(self.request.user)
        )

        admision_data = AcompanamientoService.obtener_datos_admision(comedor)
        context.update(admision_data)

        prestaciones_data = AcompanamientoService.obtener_prestaciones_detalladas(
            admision_data.get("anexo")
        )
        context.update(prestaciones_data)

        return context


class ComedoresAcompanamientoListView(ListView):
    model = Comedor
    template_name = "lista_comedores.html"
    context_object_name = "comedores"
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        busqueda = self.request.GET.get("busqueda", "")

        return AcompanamientoService.obtener_comedores_acompanamiento(user, busqueda)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("busqueda", "")
        return context
