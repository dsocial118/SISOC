from django.views.generic import ListView, DetailView
from admisiones.models.admisiones import Admision, InformeTecnicoBase, DocumentosExpediente
from comedores.models.comedor import Comedor
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
        
        admision = Admision.objects.filter(comedor=comedor).exclude(num_if__isnull=True).exclude(num_if="").order_by('-id').first()
        context["admision"] = admision

        info_relevante = None
        if admision:
            info_relevante = InformeTecnicoBase.objects.filter(admision__comedor=comedor).order_by('-id').first()
        context["info_relevante"] = info_relevante

        context["numero_if"] = admision.num_if if admision else None

        resolucion = None
        if admision:
            doc_resolucion = DocumentosExpediente.objects.filter(admision__comedor=comedor, tipo="Resolución").order_by('-creado').first()
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
