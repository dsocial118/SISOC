import logging
from django.shortcuts import get_object_or_404
from django.views import View
from django.http import JsonResponse, HttpResponseNotAllowed
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from celiaquia.models import EstadoLegajo, ExpedienteCiudadano, RevisionTecnico
from celiaquia.services.legajo_service import LegajoService
from celiaquia.services.cupo_service import CupoService, CupoNoConfigurado


logger = logging.getLogger(__name__)


def _in_group(user, name: str) -> bool:
    return user.is_authenticated and user.groups.filter(name=name).exists()


class LegajoArchivoUploadView(View):
    def dispatch(self, request, *args, **kwargs):
        self.exp_ciud = get_object_or_404(
            ExpedienteCiudadano,
            pk=kwargs["pk"],
            expediente__pk=kwargs["expediente_id"],
        )

        # ---- Permisos ----
        user = request.user
        if not user.is_authenticated:
            raise PermissionDenied("Autenticación requerida.")

        is_admin = user.is_superuser
        is_coord = _in_group(user, "CoordinadorCeliaquia")
        is_tec = _in_group(user, "TecnicoCeliaquia")
        is_prov = _in_group(user, "ProvinciaCeliaquia")

        if not (is_admin or is_coord or is_tec or is_prov):
            raise PermissionDenied("Permiso denegado.")

        # Provincia: misma provincia + estados permitidos
        if is_prov and not (is_admin or is_coord):
            owner = getattr(self.exp_ciud.expediente, "usuario_provincia", None)
            up = getattr(user, "profile", None)
            op = getattr(owner, "profile", None)
            if (
                not owner
                or not up
                or not op
                or getattr(up, "provincia_id", None)
                != getattr(op, "provincia_id", None)
            ):
                raise PermissionDenied(
                    "No pertenece a la misma provincia del expediente."
                )

            estado_nombre = getattr(
                getattr(self.exp_ciud.expediente, "estado", None), "nombre", ""
            )
            if not (
                estado_nombre == "EN_ESPERA"
                or self.exp_ciud.revision_tecnico == RevisionTecnico.SUBSANAR
            ):
                raise PermissionDenied("No puede editar archivos en el estado actual.")

        # Técnico: si querés permitirlo, que sea el asignado
        if is_tec and not (is_admin or is_coord):
            asig = getattr(self.exp_ciud.expediente, "asignacion_tecnico", None)
            if not asig or asig.tecnico_id != user.id:
                raise PermissionDenied("No sos el técnico asignado a este expediente.")

        return super().dispatch(request, *args, **kwargs)

    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        # Aceptar 'slot' o mapear desde 'campo' (archivo1/2/3)
        slot = request.POST.get("slot")
        if not slot:
            campo = (request.POST.get("campo") or "").lower().strip()
            slot_map = {"archivo1": "1", "archivo2": "2", "archivo3": "3"}
            slot = slot_map.get(campo)

        archivo_unico = request.FILES.get("archivo")
        a1 = request.FILES.get("archivo1")
        a2 = request.FILES.get("archivo2")
        a3 = request.FILES.get("archivo3")

        # Carga individual (un solo input file + slot 1/2/3)
        if archivo_unico:
            try:
                slot_int = int(slot) if slot is not None else None
            except Exception:
                return JsonResponse(
                    {"success": False, "message": "Slot inválido."}, status=400
                )
            try:
                LegajoService.subir_archivo_individual(
                    self.exp_ciud, archivo_unico, slot=slot_int
                )
                return JsonResponse(
                    {"success": True, "message": "Archivo cargado correctamente."}
                )
            except ValidationError as ve:
                return JsonResponse({"success": False, "message": str(ve)}, status=400)
            except Exception as e:
                logger.error(
                    "Error al subir archivo de legajo %s: %s",
                    self.exp_ciud.pk,
                    e,
                    exc_info=True,
                )
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Ocurrió un error al subir el archivo.",
                    },
                    status=500,
                )

        # Carga triple (archivo1/2/3)
        if a1 or a2 or a3:
            try:
                if (
                    not self.exp_ciud.archivo1
                    and not self.exp_ciud.archivo2
                    and not self.exp_ciud.archivo3
                ):
                    if not (a1 and a2 and a3):
                        return JsonResponse(
                            {
                                "success": False,
                                "message": "Debés adjuntar los tres archivos.",
                            },
                            status=400,
                        )
                    LegajoService.subir_archivos_iniciales(self.exp_ciud, a1, a2, a3)
                else:
                    if self.exp_ciud.revision_tecnico != RevisionTecnico.SUBSANAR:
                        if not (a1 and a2 and a3):
                            return JsonResponse(
                                {
                                    "success": False,
                                    "message": "Debés adjuntar los tres archivos.",
                                },
                                status=400,
                            )
                        LegajoService.subir_archivos_iniciales(
                            self.exp_ciud, a1, a2, a3
                        )
                    else:
                        LegajoService.actualizar_archivos_subsanacion(
                            self.exp_ciud, a1, a2, a3
                        )
                return JsonResponse(
                    {"success": True, "message": "Archivos cargados correctamente."}
                )
            except ValidationError as ve:
                return JsonResponse({"success": False, "message": str(ve)}, status=400)
            except Exception as e:
                logger.error(
                    "Error al subir archivos de legajo %s: %s",
                    self.exp_ciud.pk,
                    e,
                    exc_info=True,
                )
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Ocurrió un error al subir los archivos.",
                    },
                    status=500,
                )

        return JsonResponse(
            {"success": False, "message": "No se adjuntó ningún archivo."}, status=400
        )

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(["POST"])


class LegajoRechazarView(View):
    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        expediente_id = kwargs.get("expediente_id")
        pk = kwargs.get("pk")
        legajo = get_object_or_404(
            ExpedienteCiudadano, pk=pk, expediente__pk=expediente_id
        )
        try:
            CupoService.liberar_slot(
                legajo=legajo,
                usuario=request.user,
                motivo="Rechazo por técnico/coordinador",
            )
            legajo.revision_tecnico = RevisionTecnico.RECHAZADO
            legajo.save(update_fields=["revision_tecnico", "modificado_en"])
            return JsonResponse(
                {
                    "success": True,
                    "message": "Legajo rechazado y cupo liberado (si correspondía).",
                }
            )
        except CupoNoConfigurado as e:
            logger.warning("Rechazo legajo %s sin cupo configurado: %s", legajo.pk, e)
            legajo.revision_tecnico = RevisionTecnico.RECHAZADO
            legajo.save(update_fields=["revision_tecnico", "modificado_en"])
            return JsonResponse(
                {
                    "success": True,
                    "message": "Legajo rechazado. Provincia sin cupo configurado.",
                }
            )
        except ValidationError as ve:
            return JsonResponse({"success": False, "message": str(ve)}, status=400)
        except Exception as e:
            logger.error("Error al rechazar legajo %s: %s", legajo.pk, e, exc_info=True)
            return JsonResponse(
                {"success": False, "message": "Error al rechazar el legajo."},
                status=500,
            )

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(["POST"])


class LegajoSuspenderView(View):
    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        expediente_id = kwargs.get("expediente_id")
        pk = kwargs.get("pk")
        legajo = get_object_or_404(
            ExpedienteCiudadano, pk=pk, expediente__pk=expediente_id
        )
        try:
            CupoService.suspender_slot(
                legajo=legajo, usuario=request.user, motivo="Suspensión administrativa"
            )
            legajo.es_titular_activo = False
            legajo.save(update_fields=["es_titular_activo", "modificado_en"])
            return JsonResponse(
                {
                    "success": True,
                    "message": "Legajo suspendido; el cupo permanece ocupado (si correspondía).",
                }
            )
        except CupoNoConfigurado as e:
            logger.warning(
                "Suspensión legajo %s sin cupo configurado: %s", legajo.pk, e
            )
            legajo.es_titular_activo = False
            legajo.save(update_fields=["es_titular_activo", "modificado_en"])
            return JsonResponse(
                {
                    "success": True,
                    "message": "Legajo suspendido. Provincia sin cupo configurado.",
                }
            )
        except ValidationError as ve:
            return JsonResponse({"success": False, "message": str(ve)}, status=400)
        except Exception as e:
            logger.error(
                "Error al suspender legajo %s: %s", legajo.pk, e, exc_info=True
            )
            return JsonResponse(
                {"success": False, "message": "Error al suspender el legajo."},
                status=500,
            )

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(["POST"])


class LegajoBajaView(View):
    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        expediente_id = kwargs.get("expediente_id")
        pk = kwargs.get("pk")
        legajo = get_object_or_404(
            ExpedienteCiudadano, pk=pk, expediente__pk=expediente_id
        )
        try:
            CupoService.liberar_slot(
                legajo=legajo,
                usuario=request.user,
                motivo="Baja definitiva por coordinador",
            )
            legajo.es_titular_activo = False
            legajo.revision_tecnico = RevisionTecnico.RECHAZADO
            legajo.save(
                update_fields=["es_titular_activo", "revision_tecnico", "modificado_en"]
            )
            return JsonResponse(
                {
                    "success": True,
                    "message": "Baja registrada y cupo liberado (si correspondía).",
                }
            )
        except CupoNoConfigurado as e:
            logger.warning("Baja legajo %s sin cupo configurado: %s", legajo.pk, e)
            legajo.es_titular_activo = False
            legajo.revision_tecnico = RevisionTecnico.RECHAZADO
            legajo.save(
                update_fields=["es_titular_activo", "revision_tecnico", "modificado_en"]
            )
            return JsonResponse(
                {
                    "success": True,
                    "message": "Baja registrada. Provincia sin cupo configurado.",
                }
            )
        except ValidationError as ve:
            return JsonResponse({"success": False, "message": str(ve)}, status=400)
        except Exception as e:
            logger.error(
                "Error al dar de baja legajo %s: %s", legajo.pk, e, exc_info=True
            )
            return JsonResponse(
                {"success": False, "message": "Error al dar de baja el legajo."},
                status=500,
            )

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(["POST"])


class LegajoSubsanarView(View):
    @method_decorator(csrf_protect)
    def post(self, request, pk, legajo_id):
        user = request.user
        is_admin = user.is_authenticated and user.is_superuser
        is_coord = _in_group(user, "CoordinadorCeliaquia")
        is_tec = _in_group(user, "TecnicoCeliaquia")

        if not (is_admin or is_coord or is_tec):
            raise PermissionDenied("Permiso denegado.")

        legajo = get_object_or_404(ExpedienteCiudadano, pk=legajo_id, expediente__pk=pk)

        if is_tec and not (is_admin or is_coord):
            asig = getattr(legajo.expediente, "asignacion_tecnico", None)
            if not asig or asig.tecnico_id != user.id:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "No sos el técnico asignado a este expediente.",
                    },
                    status=403,
                )

        # Aceptar 'motivo' o 'comentario'
        comentario = (
            request.POST.get("comentario") or request.POST.get("motivo") or ""
        ).strip()
        if not comentario:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Debe ingresar un comentario/motivo de subsanación.",
                },
                status=400,
            )

        estado_sub, _ = EstadoLegajo.objects.get_or_create(
            nombre="PENDIENTE_SUBSANACION"
        )
        legajo.estado = estado_sub
        legajo.revision_tecnico = (
            "SUBSANAR"  # si usás constante: RevisionTecnico.SUBSANAR
        )

        update_fields = ["estado", "revision_tecnico", "modificado_en"]

        if hasattr(legajo, "comentario_subsanacion"):
            legajo.comentario_subsanacion = comentario
            update_fields.append("comentario_subsanacion")
        elif hasattr(legajo, "observacion_tecnico"):
            legajo.observacion_tecnico = comentario
            update_fields.append("observacion_tecnico")

        legajo.save(update_fields=update_fields)

        logger.info(
            "Subsanación solicitada: legajo=%s por user=%s: %s",
            legajo.pk,
            user.id,
            comentario,
        )

        return JsonResponse(
            {
                "success": True,
                "message": "Subsanación solicitada. El registro quedó en SUBSANAR para que la provincia actualice archivos.",
                "estado": "PENDIENTE_SUBSANACION",
            }
        )

    def get(self, *_a, **_k):
        return HttpResponseNotAllowed(["POST"])
