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

logger = logging.getLogger(__name__)


def _in_group(user, name):
    return user.is_authenticated and user.groups.filter(name=name).exists()


def _same_owner(user, exp) -> bool:
    # si tu modelo guarda así al dueño del expediente:
    return exp.usuario_provincia_id == user.id


class ExpedienteConfirmSubsanacionView(View):
    def get(self, *_a, **_k):
        return HttpResponseNotAllowed(["POST"])

    @method_decorator(csrf_protect)
    def post(self, request, pk):
        user = request.user
        if not user.is_authenticated:
            raise PermissionDenied("Autenticación requerida.")

        exp = get_object_or_404(Expediente, pk=pk)

        is_admin = user.is_superuser
        is_prov = _in_group(user, "ProvinciaCeliaquia")

        if not (is_admin or (is_prov and _same_owner(user, exp))):
            raise PermissionDenied(
                "No tenés permiso para confirmar la subsanación de este expediente."
            )

        # Legajos en SUBSANAR con faltantes
        q_falta = (
            Q(archivo1__isnull=True)
            | Q(archivo1="")
            | Q(archivo2__isnull=True)
            | Q(archivo2="")
            | Q(archivo3__isnull=True)
            | Q(archivo3="")
        )
        faltan = ExpedienteCiudadano.objects.filter(
            expediente=exp, revision_tecnico=RevisionTecnico.SUBSANAR
        ).filter(q_falta)

        if faltan.exists():
            dnis = list(faltan.values_list("ciudadano__documento", flat=True)[:10])
            return JsonResponse(
                {
                    "success": False,
                    "error": "Hay legajos en SUBSANAR que aún no tienen los 3 archivos.",
                    "ejemplo_dnis": dnis,
                },
                status=400,
            )

        # Cambiar SUBSANAR → SUBSANADO
        actualizados = ExpedienteCiudadano.objects.filter(
            expediente=exp, revision_tecnico=RevisionTecnico.SUBSANAR
        ).update(
            revision_tecnico=RevisionTecnico.SUBSANADO,
            modificado_en=timezone.now(),
            subsanacion_enviada_en=timezone.now(),
            subsanacion_usuario=user,
        )

        logger.info(
            "Confirmar subsanación exp=%s user=%s: %s legajos",
            exp.pk,
            user.id,
            actualizados,
        )

        return JsonResponse(
            {
                "success": True,
                "message": f"Se confirmaron {actualizados} legajos como SUBSANADO.",
            }
        )
