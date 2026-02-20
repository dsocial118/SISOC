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
from celiaquia.permissions import can_edit_legajo_files, can_review_legajo
from core.soft_delete_preview import build_delete_preview
from core.soft_delete_views import is_soft_deletable_instance


logger = logging.getLogger("django")


def _in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


class LegajoArchivoUploadView(View):
    def dispatch(self, request, *args, **kwargs):
        self.exp_ciud = get_object_or_404(
            ExpedienteCiudadano,
            pk=kwargs["pk"],
            expediente__pk=kwargs["expediente_id"],
        )

        # Validar permisos usando función centralizada
        try:
            can_edit_legajo_files(request.user, self.exp_ciud.expediente, self.exp_ciud)
        except PermissionDenied as e:
            logger.warning(
                "Permission denied for user %s on legajo %s: %s",
                request.user.id,
                self.exp_ciud.pk,
                str(e),
            )
            return JsonResponse(
                {
                    "success": False,
                    "message": "No tenés permiso para realizar esta acción.",
                },
                status=403,
            )

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
            except (ValueError, TypeError):
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

        # Carga doble (archivo2/3)
        if a2 or a3:
            try:
                if not self.exp_ciud.archivo2 and not self.exp_ciud.archivo3:
                    if not (a2 and a3):
                        return JsonResponse(
                            {
                                "success": False,
                                "message": "Debés adjuntar los dos archivos requeridos.",
                            },
                            status=400,
                        )
                    LegajoService.subir_archivos_iniciales(self.exp_ciud, None, a2, a3)
                else:
                    if self.exp_ciud.revision_tecnico != RevisionTecnico.SUBSANAR:
                        if not (a2 and a3):
                            return JsonResponse(
                                {
                                    "success": False,
                                    "message": "Debés adjuntar los dos archivos requeridos.",
                                },
                                status=400,
                            )
                        LegajoService.subir_archivos_iniciales(
                            self.exp_ciud, None, a2, a3
                        )
                    else:
                        LegajoService.actualizar_archivos_subsanacion(
                            self.exp_ciud, None, a2, a3
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

        # Validar permisos usando función centralizada
        can_review_legajo(request.user, legajo.expediente)
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
        # Validación de permisos
        user = request.user
        if not user.is_authenticated:
            raise PermissionDenied("Autenticación requerida.")

        is_admin = user.is_superuser
        is_coord = _in_group(user, "CoordinadorCeliaquia")
        is_tec = _in_group(user, "TecnicoCeliaquia")

        if not (is_admin or is_coord or is_tec):
            raise PermissionDenied("Permiso denegado.")

        expediente_id = kwargs.get("expediente_id")
        pk = kwargs.get("pk")
        legajo = get_object_or_404(
            ExpedienteCiudadano, pk=pk, expediente__pk=expediente_id
        )

        # Validar que el técnico esté asignado al expediente
        if is_tec and not (is_admin or is_coord):
            asignaciones = legajo.expediente.asignaciones_tecnicos.filter(tecnico=user)
            if not asignaciones.exists():
                raise PermissionDenied("No sos el técnico asignado a este expediente.")
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
        # Validación de permisos - solo coordinadores y admins pueden dar de baja
        user = request.user
        if not user.is_authenticated:
            raise PermissionDenied("Autenticación requerida.")

        is_admin = user.is_superuser
        is_coord = _in_group(user, "CoordinadorCeliaquia")

        if not (is_admin or is_coord):
            raise PermissionDenied("Solo coordinadores pueden dar de baja legajos.")

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
            asignaciones = legajo.expediente.asignaciones_tecnicos.filter(tecnico=user)
            if not asignaciones.exists():
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
        legajo.revision_tecnico = RevisionTecnico.SUBSANAR

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


class LegajoEliminarView(View):
    @method_decorator(csrf_protect)
    def post(self, request, pk, legajo_id):
        from django.db import transaction

        user = request.user
        is_coord = _in_group(user, "CoordinadorCeliaquia")

        if not (user.is_superuser or is_coord):
            return JsonResponse(
                {
                    "success": False,
                    "message": "Solo coordinadores pueden eliminar legajos.",
                },
                status=403,
            )

        try:
            legajo = get_object_or_404(
                ExpedienteCiudadano, pk=legajo_id, expediente__pk=pk
            )

            get_data = getattr(request, "GET", {})
            post_data = getattr(request, "POST", {})
            preview_enabled = str(
                post_data.get("preview") or get_data.get("preview") or ""
            )
            if preview_enabled in {"1", "true", "True"} and is_soft_deletable_instance(
                legajo
            ):
                return JsonResponse(
                    {
                        "success": True,
                        "preview": build_delete_preview(legajo),
                    }
                )

            with transaction.atomic():
                # Liberar cupo ocupado antes de eliminar el legajo
                try:
                    CupoService.liberar_slot(
                        legajo=legajo,
                        usuario=user,
                        motivo="Eliminación manual del legajo",
                    )
                except CupoNoConfigurado as e:
                    logger.warning(
                        "No se pudo liberar cupo para legajo %s: %s", legajo_id, e
                    )
                except Exception as e:  # pragma: no cover - log y abortar
                    logger.error(
                        "Error liberando cupo antes de eliminar legajo %s: %s",
                        legajo_id,
                        e,
                        exc_info=True,
                    )
                    raise

                # Eliminar registros relacionados primero
                from celiaquia.models import CupoMovimiento, PagoNomina

                # Eliminar movimientos de cupo relacionados
                CupoMovimiento.objects.filter(legajo=legajo).delete()

                # Eliminar registros de pago relacionados
                PagoNomina.objects.filter(legajo=legajo).delete()

                # Eliminar el legajo
                if is_soft_deletable_instance(legajo):
                    legajo.delete(user=user, cascade=True)
                else:
                    legajo.delete()

            return JsonResponse(
                {"success": True, "message": "Legajo eliminado correctamente."}
            )

        except Exception as e:
            logger.error(
                "Error al eliminar legajo %s: %s", legajo_id, str(e), exc_info=True
            )
            return JsonResponse(
                {
                    "success": False,
                    "message": "Ocurrió un error interno. Por favor intente nuevamente o contacte al administrador.",
                },
                status=500,
            )

    def get(self, *_a, **_k):
        return HttpResponseNotAllowed(["POST"])
