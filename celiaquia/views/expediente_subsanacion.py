import logging
from django.views import View
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.utils import timezone

from celiaquia.models import Expediente, ExpedienteCiudadano, RevisionTecnico
from celiaquia.permissions import can_confirm_subsanacion
from celiaquia.utils import error_response, success_response

logger = logging.getLogger(__name__)


def _in_group(user, name):
    """Verifica si el usuario pertenece a un grupo específico."""
    return user.is_authenticated and user.groups.filter(name=name).exists()


def _same_owner(user, exp) -> bool:
    """Verifica si el usuario es el propietario del expediente."""
    return exp.usuario_provincia_id == user.id


class ExpedienteConfirmSubsanacionView(View):
    """Vista para confirmar la subsanación de legajos en un expediente."""
    def get(self, *_a, **_k):
        return HttpResponseNotAllowed(["POST"])

    @method_decorator(csrf_protect)
    def post(self, request, pk):
        exp = get_object_or_404(Expediente, pk=pk)
        
        # Validar permisos usando función centralizada
        can_confirm_subsanacion(request.user, exp)

        # Legajos en SUBSANAR con faltantes (solo archivo2 y archivo3 son obligatorios)
        query_archivos_faltantes = (
            Q(archivo2__isnull=True)
            | Q(archivo2="")
            | Q(archivo3__isnull=True)
            | Q(archivo3="")
        )
        legajos_sin_archivos = ExpedienteCiudadano.objects.filter(
            expediente=exp, revision_tecnico=RevisionTecnico.SUBSANAR
        ).filter(query_archivos_faltantes)

        if legajos_sin_archivos.exists():
            dnis = list(legajos_sin_archivos.values_list("ciudadano__documento", flat=True)[:10])
            return error_response(
                "Hay legajos en SUBSANAR que aún no tienen los archivos obligatorios (archivo2 y archivo3).",
                status=400,
                extra_data={"ejemplo_dnis": dnis}
            )

        # Cambiar SUBSANAR → SUBSANADO
        actualizados = ExpedienteCiudadano.objects.filter(
            expediente=exp, revision_tecnico=RevisionTecnico.SUBSANAR
        ).update(
            revision_tecnico=RevisionTecnico.SUBSANADO,
            modificado_en=timezone.now(),
            subsanacion_enviada_en=timezone.now(),
            subsanacion_usuario=request.user,
        )

        logger.info(
            "Subsanación confirmada - Expediente: %s, Usuario: %s, Legajos actualizados: %s",
            exp.pk,
            request.user.id,
            actualizados,
        )

        return success_response(
            f"Se confirmaron {actualizados} legajos como SUBSANADO."
        )
