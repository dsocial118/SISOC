import logging
from django.views import View
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q
from django.utils import timezone

from celiaquia.models import Expediente, ExpedienteCiudadano, RevisionTecnico
from celiaquia.permissions import can_confirm_subsanacion
from celiaquia.utils import error_response, success_response

logger = logging.getLogger("django")


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

        # Verificar si es confirmación individual o masiva
        legajo_id = request.POST.get("legajo_id")

        if legajo_id:
            # Confirmación individual
            legajo = get_object_or_404(
                ExpedienteCiudadano,
                pk=legajo_id,
                expediente=exp,
                revision_tecnico=RevisionTecnico.SUBSANAR,
            )

            # Verificar que tenga los archivos obligatorios
            if not legajo.archivo2 or not legajo.archivo3:
                return error_response(
                    "El legajo no tiene los archivos obligatorios (archivo2 y archivo3).",
                    status=400,
                )

            # Cambiar a SUBSANADO
            legajo.revision_tecnico = RevisionTecnico.SUBSANADO
            legajo.modificado_en = timezone.now()
            legajo.subsanacion_enviada_en = timezone.now()
            legajo.subsanacion_usuario = request.user
            legajo.save()

            logger.info(
                "Subsanación individual confirmada - Legajo: %s, Usuario: %s",
                legajo.pk,
                request.user.id,
            )

            return success_response("Subsanación confirmada correctamente.")

        else:
            # Confirmación masiva (todos los legajos en SUBSANAR)
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
                dnis = list(
                    legajos_sin_archivos.values_list("ciudadano__documento", flat=True)[
                        :10
                    ]
                )
                return error_response(
                    "Hay legajos en SUBSANAR que aún no tienen los archivos obligatorios (archivo2 y archivo3).",
                    status=400,
                    extra_data={"ejemplo_dnis": dnis},
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
                "Subsanación masiva confirmada - Expediente: %s, Usuario: %s, Legajos actualizados: %s",
                exp.pk,
                request.user.id,
                actualizados,
            )

            return success_response(
                f"Se confirmaron {actualizados} legajos como SUBSANADO."
            )
