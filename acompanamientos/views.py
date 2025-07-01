from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.views.decorators.http import require_POST
from django.db.models import Q
from admisiones.models.admisiones import (
    Admision,
    InformeTecnico,
    DocumentosExpediente,
    Anexo,
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
        context["hitos"] = AcompanamientoService.obtener_hitos(comedor)
        context["es_tecnico_comedor"] = (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name="Tecnico Comedor").exists()
        )
        admision = (
            Admision.objects.filter(comedor=comedor)
            .exclude(legales_num_if__isnull=True)
            .exclude(legales_num_if="")
            .order_by("-id")
            .first()
        )
        context["admision"] = admision

        info_relevante = None
        resolucion = None
        doc_resolucion = None

        if admision:
            info_relevante = (
                InformeTecnico.objects.filter(admision=admision).order_by("-id").first()
            )

            # Obtener el anexo
            anexo = Anexo.objects.filter(admision=admision).first()
            context["anexo"] = anexo

            doc_resolucion = (
                DocumentosExpediente.objects.filter(
                    admision__comedor=comedor, tipo="Resolución"
                )
                .order_by("-creado")
                .first()
            )
        if doc_resolucion:
            resolucion = doc_resolucion.value or doc_resolucion.nombre

        # Asignar valores al contexto
        context["info_relevante"] = info_relevante
        context["numero_if"] = admision.legales_num_if if admision else None
        context["numero_resolucion"] = resolucion
        # TODO: Implementar lógica real para vencimiento de mandato cuando esté la feature
        context["vencimiento_mandato"] = "Pendiente de implementación"

        # Prestaciones
        if anexo:
            # Crear estructura de prestaciones por día usando datos del anexo
            dias = [
                "lunes",
                "martes",
                "miercoles",
                "jueves",
                "viernes",
                "sabado",
                "domingo",
            ]
            tipos_comida = ["desayuno", "almuerzo", "merienda", "cena"]

            # Crear estructura de tabla para mostrar prestaciones por día
            prestaciones_por_dia = []
            prestaciones_totales = []

            for tipo in tipos_comida:
                fila = {"tipo": tipo.capitalize()}
                total_semanal = 0

                for dia in dias:
                    campo_nombre = f"{tipo}_{dia}"
                    cantidad = getattr(anexo, campo_nombre, 0) if anexo else 0
                    fila[dia] = cantidad
                    total_semanal += cantidad or 0  # Sumar para el total semanal

                prestaciones_por_dia.append(fila)
                prestaciones_totales.append(
                    {"tipo": tipo.capitalize(), "cantidad": total_semanal}
                )

            context["prestaciones_por_dia"] = prestaciones_por_dia
            context["prestaciones_dias"] = (
                prestaciones_totales  # Usar totales calculados desde anexo
            )
            context["dias_semana"] = [dia.capitalize() for dia in dias]
        else:
            context["prestaciones_por_dia"] = []
            context["prestaciones_dias"] = []
            context["dias_semana"] = []

        return context


class ComedoresAcompanamientoListView(ListView):
    model = Comedor
    template_name = "lista_comedores.html"
    context_object_name = "comedores"
    paginate_by = 10  # Cantidad de resultados por página

    def get_queryset(self):
        user = self.request.user
        busqueda = self.request.GET.get("busqueda", "").strip().lower()

        # Filtramos las admisiones con estado=2 (Finalizada)
        admisiones = Admision.objects.filter(estado=2, enviado_acompaniamiento=True)

        # Si no es superusuario, filtramos por dupla asignada

        if (
            not user.is_superuser
            and not user.groups.filter(name="Area Legales").exists()
        ):
            admisiones = admisiones.filter(
                Q(comedor__dupla__abogado=user) | Q(comedor__dupla__tecnico=user)
            )

        # Obtenemos los IDs de los comedores que tienen admisiones finalizadas
        comedor_ids = admisiones.values_list("comedor_id", flat=True).distinct()

        # Filtramos los comedores
        queryset = Comedor.objects.filter(id__in=comedor_ids).select_related(
            "referente", "tipocomedor", "provincia"
        )

        # Aplicamos búsqueda global
        if busqueda:
            queryset = queryset.filter(
                Q(nombre__icontains=busqueda)
                | Q(provincia__nombre__icontains=busqueda)
                | Q(tipocomedor__nombre__icontains=busqueda)
                | Q(calle__icontains=busqueda)
                | Q(numero__icontains=busqueda)
                | Q(referente__nombre__icontains=busqueda)
                | Q(referente__apellido__icontains=busqueda)
                | Q(referente__celular__icontains=busqueda)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("busqueda", "")
        return context
