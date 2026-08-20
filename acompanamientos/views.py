from urllib.parse import parse_qs, urlparse

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse

from acompanamientos.acompanamiento_service import AcompanamientoService
from acompanamientos.services.filter_config import get_filters_ui_config
from comedores.models import Comedor
from comedores.services.comedor_service import ComedorService
from admisiones.models.admisiones import Admision, InformeTecnico
from core.services.column_preferences import build_columns_context_for_custom_cells
from core.services.favorite_filters import SeccionesFiltrosFavoritos
from core.services.list_ordering import build_ordering_header
from core.security import safe_redirect
from iam.services import user_has_permission_code


def _parse_admision_id(raw_admision_id):
    if raw_admision_id and raw_admision_id.isdigit():
        return int(raw_admision_id)
    return None


def _extract_admision_id_from_referer(request):
    referer = request.META.get("HTTP_REFERER")
    if not referer:
        return None
    admision_ids = parse_qs(urlparse(referer).query).get("admision_id", [None])
    return _parse_admision_id(admision_ids[0])


def _build_detalle_acompanamiento_url(comedor_id, admision_id=None):
    url = reverse("detalle_acompanamiento", kwargs={"comedor_id": comedor_id})
    if admision_id:
        return f"{url}?admision_id={admision_id}"
    return url


@login_required
@require_POST
def restaurar_hito(request, comedor_id):
    campo = request.POST.get("campo")
    admision_id = _parse_admision_id(
        request.POST.get("admision_id") or request.GET.get("admision_id")
    ) or _extract_admision_id_from_referer(request)
    comedor = ComedorService.get_scoped_comedor_or_404(comedor_id, request.user)
    hito = AcompanamientoService.obtener_hitos(comedor, admision_id=admision_id)

    if not hito:
        messages.error(
            request,
            "No se encontraron hitos para el convenio seleccionado.",
        )
        return safe_redirect(
            request,
            default=_build_detalle_acompanamiento_url(comedor_id, admision_id),
            target=request.META.get("HTTP_REFERER"),
        )

    acompanamiento = hito.acompanamiento
    if acompanamiento and not acompanamiento.es_gestionable:
        messages.error(
            request,
            "El acompañamiento está finalizado o cerrado: no admite modificaciones.",
        )
        return safe_redirect(
            request,
            default=_build_detalle_acompanamiento_url(comedor_id, admision_id),
            target=request.META.get("HTTP_REFERER"),
        )

    # Verifica si el campo existe en el modelo
    if hasattr(hito, campo) and campo not in ["id", "acompanamiento", "fecha"]:
        setattr(hito, campo, False)  # Cambia el valor del campo a False (0)
        hito.save()
        messages.success(
            request, f"El campo '{campo}' ha sido restaurado correctamente."
        )
    else:
        messages.error(request, f"El campo '{campo}' no existe en el modelo Hitos.")

    # Redirige a la página anterior
    return safe_redirect(
        request,
        default=_build_detalle_acompanamiento_url(comedor_id, admision_id),
        target=request.META.get("HTTP_REFERER"),
    )


@login_required
@require_POST
def finalizar_acompanamiento(request, comedor_id):
    """Marca el acompañamiento del convenio seleccionado como finalizado."""
    admision_id = _parse_admision_id(
        request.POST.get("admision_id")
    ) or _extract_admision_id_from_referer(request)
    comedor = ComedorService.get_scoped_comedor_or_404(comedor_id, request.user)

    _, error = AcompanamientoService.finalizar_acompanamiento(
        comedor, admision_id, request.user
    )

    if error:
        messages.error(request, error)
    else:
        messages.success(
            request,
            "El acompañamiento fue finalizado. Ya no es posible operar con esta "
            "admisión en SISOC.",
        )

    return safe_redirect(
        request,
        default=_build_detalle_acompanamiento_url(comedor_id, admision_id),
        target=request.META.get("HTTP_REFERER"),
    )


class AcompanamientoDetailView(LoginRequiredMixin, DetailView):
    model = Comedor
    template_name = "acompañamiento_detail.html"
    context_object_name = "comedor"
    pk_url_kwarg = "comedor_id"

    def get_queryset(self):
        return ComedorService.get_scoped_comedor_queryset(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor = self.object
        admision_id = _parse_admision_id(self.request.GET.get("admision_id"))

        context["es_tecnico_comedor"] = (
            self.request.user.is_superuser
            or user_has_permission_code(self.request.user, "auth.role_tecnico_comedor")
        )

        admisiones_disponibles = list(
            AcompanamientoService.obtener_admisiones_para_selector(comedor)
        )
        context["admisiones_disponibles"] = admisiones_disponibles

        activas = [a for a in admisiones_disponibles if a.activa]
        context["tiene_multiples_activos"] = len(activas) > 1

        # Configuración de todos los hitos para evitar repetición en el template
        context["hitos_config"] = [
            {"campo": "retiro_tarjeta", "descripcion": "Retiro de Tarjeta"},
            {"campo": "habilitacion_tarjeta", "descripcion": "Habilitación de Tarjeta"},
            {
                "campo": "alta_usuario_plataforma",
                "descripcion": "Alta de Usuario en Plataforma",
            },
            {
                "campo": "capacitacion_realizada",
                "descripcion": "Capacitación Sincrónica Realizada",
            },
            {
                "campo": "capacitacion_fch_realizada",
                "descripcion": "Capacitación Formando Capital Humano Realizada",
            },
            {
                "campo": "notificacion_acreditacion_1",
                "descripcion": "Notificación de primera acreditación",
            },
            {
                "campo": "notificacion_acreditacion_2",
                "descripcion": "Notificación de acreditación mes 2",
            },
            {
                "campo": "notificacion_acreditacion_3",
                "descripcion": "Notificación de acreditación mes 3",
            },
            {
                "campo": "notificacion_acreditacion_4",
                "descripcion": "Notificación de acreditación mes 4",
            },
            {
                "campo": "notificacion_acreditacion_5",
                "descripcion": "Notificación de acreditación mes 5",
            },
            {
                "campo": "notificacion_acreditacion_6",
                "descripcion": "Notificación de acreditación mes 6",
            },
            {
                "campo": "nomina_entregada_inicial",
                "descripcion": "Nómina entregada inicial",
            },
            {"campo": "nomina_alta_baja_2", "descripcion": "Nómina Alta/baja mes 2"},
            {"campo": "nomina_alta_baja_3", "descripcion": "Nómina Alta/baja mes 3"},
            {"campo": "nomina_alta_baja_4", "descripcion": "Nómina Alta/baja mes 4"},
            {"campo": "nomina_alta_baja_5", "descripcion": "Nómina Alta/baja mes 5"},
            {"campo": "nomina_alta_baja_6", "descripcion": "Nómina Alta/baja mes 6"},
            {
                "campo": "certificado_prestaciones_1",
                "descripcion": "Certificado mensual de prestaciones mes: 1",
            },
            {
                "campo": "certificado_prestaciones_2",
                "descripcion": "Certificado mensual de prestaciones mes: 2",
            },
            {
                "campo": "certificado_prestaciones_3",
                "descripcion": "Certificado mensual de prestaciones mes: 3",
            },
            {
                "campo": "certificado_prestaciones_4",
                "descripcion": "Certificado mensual de prestaciones mes: 4",
            },
            {
                "campo": "certificado_prestaciones_5",
                "descripcion": "Certificado mensual de prestaciones mes: 5",
            },
            {
                "campo": "certificado_prestaciones_6",
                "descripcion": "Certificado mensual de prestaciones mes: 6",
            },
        ]

        datos_admision = AcompanamientoService.obtener_datos_admision(
            comedor, admision_id=admision_id
        )
        if (
            not datos_admision.get("admision")
            and not admision_id
            and admisiones_disponibles
        ):
            admision_id = admisiones_disponibles[0].id
            datos_admision = AcompanamientoService.obtener_datos_admision(
                comedor, admision_id=admision_id
            )

        admision = datos_admision.get("admision")
        info_relevante = datos_admision.get("info_relevante")
        hitos_admision_id = admision.id if admision else admision_id
        admision_id_activa = admision.id if admision else None

        context["admision_id_activa"] = admision_id_activa
        context["hitos"] = AcompanamientoService.obtener_hitos(
            comedor, admision_id=hitos_admision_id
        )
        context["fechas_hitos"] = AcompanamientoService.obtener_fechas_hitos(
            comedor, admision_id=admision_id_activa
        )

        context["admision"] = admision
        context["informe_tecnico_complementario"] = (
            InformeTecnico.objects.filter(
                admision=admision,
                estado_formulario="finalizado",
            )
            .order_by("-id")
            .first()
            if admision and context["es_tecnico_comedor"]
            else None
        )
        context["info_relevante"] = info_relevante
        context["numero_if"] = datos_admision.get("numero_if")
        context["numero_disposicion"] = datos_admision.get("numero_disposicion")

        acompanamiento_obj = (
            getattr(admision, "acompanamiento", None) if admision else None
        )
        context["nro_convenio"] = (
            acompanamiento_obj.nro_convenio if acompanamiento_obj else ""
        )
        context["acompanamiento"] = acompanamiento_obj
        context["acompanamiento_finalizado"] = bool(
            acompanamiento_obj and acompanamiento_obj.finalizado
        )
        context["puede_finalizar_acompanamiento"] = bool(
            acompanamiento_obj and acompanamiento_obj.puede_finalizarse
        )
        context["acompanamiento_gestionable"] = bool(
            acompanamiento_obj and acompanamiento_obj.es_gestionable
        )

        prestaciones_detalle = AcompanamientoService.obtener_prestaciones_detalladas(
            info_relevante
        )

        context["prestaciones_por_dia"] = prestaciones_detalle.get(
            "prestaciones_por_dia", []
        )
        context["prestaciones_dias"] = prestaciones_detalle.get("prestaciones_dias", [])
        context["dias_semana"] = prestaciones_detalle.get("dias_semana", [])

        return context


ACOMPANAMIENTOS_LIST_HEADERS_KEY = "acompanamientos_list"


@method_decorator(ensure_csrf_cookie, name="dispatch")
class AcompanamientosListView(LoginRequiredMixin, ListView):
    """Listado con una fila por acompañamiento, incluyendo el histórico."""

    model = Admision
    template_name = "lista_comedores.html"
    context_object_name = "comedores"
    paginate_by = 10

    def get_queryset(self):
        return AcompanamientoService.obtener_acompanamientos(
            self.request.user, self.request
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("busqueda", "")

        # Configuración para data_table
        headers = [
            {"key": "id", "title": "ID"},
            build_ordering_header(self.request, key="nombre", title="Nombre"),
            {"key": "convenio", "title": "Convenio"},
            {"key": "organizacion", "title": "Organización"},
            {"key": "expediente", "title": "N° Expediente"},
            {"key": "provincia", "title": "Provincia"},
            {"key": "dupla", "title": "Dupla"},
            {"key": "estado", "title": "Estado"},
            {"key": "estado_acompanamiento", "title": "Estado del acompañamiento"},
            {"key": "modificado", "title": "Última Modificación"},
        ]

        # Usar modo personalizado para acceder a campos relacionados
        context["custom_cells"] = True

        filas = AcompanamientoService.preparar_datos_tabla_acompanamientos(
            context["comedores"]
        )
        context.update(
            build_columns_context_for_custom_cells(
                self.request,
                ACOMPANAMIENTOS_LIST_HEADERS_KEY,
                headers,
                filas,
                items_key="comedores",
            )
        )

        context["custom_actions"] = True
        context.update(
            {
                "reset_url": reverse("lista_comedores_acompanamiento"),
                "filters_mode": True,
                "filters_config": get_filters_ui_config(),
                "filters_action": reverse("lista_comedores_acompanamiento"),
                "seccion_filtros_favoritos": (
                    SeccionesFiltrosFavoritos.ACOMPANAMIENTOS
                ),
            }
        )
        return context


@login_required
def comedores_acompanamiento_ajax(request):
    """
    Vista AJAX para búsqueda dinámica de acompañamientos
    """
    busqueda = request.GET.get("busqueda", "").strip()
    page = request.GET.get("page", 1)

    user = request.user
    acompanamientos = AcompanamientoService.obtener_acompanamientos(
        user, busqueda.lower()
    )

    paginator = Paginator(
        acompanamientos, 10
    )  # mismo paginate_by que AcompanamientosListView

    try:
        page_obj = paginator.get_page(page)
    except (ValueError, TypeError):
        page_obj = paginator.get_page(1)

    table_html = render_to_string(
        "acompanamientos/partials/comedor_rows.html",
        {"admisiones": page_obj.object_list},
        request=request,
    )

    pagination_html = render_to_string(
        "components/pagination.html",
        {
            "is_paginated": page_obj.has_other_pages(),
            "page_obj": page_obj,
            "query": busqueda,
            "prev_text": "Volver",
            "next_text": "Continuar",
        },
        request=request,
    )

    return JsonResponse(
        {
            "html": table_html,
            "pagination_html": pagination_html,
            "count": paginator.count,
            "current_page": page_obj.number,
            "total_pages": paginator.num_pages,
            "has_previous": page_obj.has_previous(),
            "has_next": page_obj.has_next(),
        }
    )
