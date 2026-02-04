import os
from datetime import datetime
from django.conf import settings
from django.db import models
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.core.files.base import ContentFile
from io import BytesIO
from django.utils import timezone

from admisiones.models.admisiones import (
    Admision,
    EstadoAdmision,
    TipoConvenio,
    Documentacion,
    ArchivoAdmision,
    InformeTecnico,
    InformeTecnicoPDF,
    InformeComplementario,
)
from admisiones.forms.admisiones_forms import (
    CaratularForm,
    IFInformeTecnicoForm,
)
from acompanamientos.acompanamiento_service import AcompanamientoService
from .docx_service import DocumentTemplateService, TextFormatterService
from core.services.advanced_filters import AdvancedFilterEngine
from admisiones.services.admisiones_filter_config import (
    FIELD_MAP as ADMISION_FILTER_MAP,
    FIELD_TYPES as ADMISION_FIELD_TYPES,
    TEXT_OPS as ADMISION_TEXT_OPS,
    NUM_OPS as ADMISION_NUM_OPS,
    DATE_OPS as ADMISION_DATE_OPS,
    CHOICE_OPS as ADMISION_CHOICE_OPS,
)

from django.db.models import Q
import logging

logger = logging.getLogger("django")

ADMISION_ADVANCED_FILTER = AdvancedFilterEngine(
    field_map=ADMISION_FILTER_MAP,
    field_types=ADMISION_FIELD_TYPES,
    allowed_ops={
        "text": ADMISION_TEXT_OPS,
        "number": ADMISION_NUM_OPS,
        "date": ADMISION_DATE_OPS,
        "choice": ADMISION_CHOICE_OPS,
    },
)


class AdmisionService:

    @staticmethod
    def _normalize_estado_display(estado):

        estado_limpio = (estado or "").strip()

        if not estado_limpio:

            estado_limpio = "pendiente"

        mapping = {
            "pendiente": ("Pendiente", "pendiente"),
            "Documento adjunto": ("Documento adjunto", "Documento adjunto"),
            "a validar abogado": ("A Validar Abogado", "A Validar Abogado"),
            "rectificar": ("Rectificar", "Rectificar"),
            "aceptado": ("Aceptado", "Aceptado"),
        }

        display, valor = mapping.get(
            estado_limpio.lower(), (estado_limpio, estado_limpio)
        )

        return display, valor

    @staticmethod
    def _estado_display_y_valor(estado):

        display, valor = AdmisionService._normalize_estado_display(estado)

        return display, valor

    @staticmethod
    def _estados_resumen():

        return [
            "Pendiente",
            "Documento adjunto",
            "A Validar Abogado",
            "Rectificar",
            "Aceptado",
        ]

    @staticmethod
    def _resumen_vacio():

        return {estado: 0 for estado in AdmisionService._estados_resumen()}

    @staticmethod
    def _resumen_documentos(documentos, personalizados):

        resumen = AdmisionService._resumen_vacio()

        for item in (documentos or []) + (personalizados or []):

            display, _ = AdmisionService._normalize_estado_display(item.get("estado"))

            if display not in resumen:

                resumen[display] = 0

            resumen[display] += 1

        return resumen

    @staticmethod
    def _stats_from_resumen(resumen, obligatorios_totales, obligatorios_completos):

        stats = {
            "pendientes": resumen.get("Pendiente", 0),
            "a_validar": resumen.get("Documento adjunto", 0),
            "a_validar_abogado": resumen.get("A Validar Abogado", 0),
            "rectificar": resumen.get("Rectificar", 0),
            "aceptados": resumen.get("Aceptado", 0),
            "obligatorios_total": obligatorios_totales,
            "obligatorios_completos": obligatorios_completos,
        }

        return stats

    @staticmethod
    def _archivo_nombre(archivo):

        if getattr(archivo, "nombre_personalizado", None):

            return archivo.nombre_personalizado

        if getattr(archivo, "archivo", None):

            return os.path.basename(archivo.archivo.name)

        return "Documento adicional"

    @staticmethod
    def _serialize_documentacion(documentacion, archivo=None):

        estado = archivo.estado if archivo else "pendiente"

        estado_display, estado_valor = AdmisionService._estado_display_y_valor(estado)

        row_id = (
            str(documentacion.id)
            if documentacion
            else (f"custom-{archivo.id}" if archivo else "")
        )

        return {
            "id": archivo.id if archivo else documentacion.id,
            "documentacion_id": documentacion.id,
            "archivo_id": archivo.id if archivo else None,
            "nombre": documentacion.nombre,
            "obligatorio": documentacion.obligatorio,
            "estado": estado_display,
            "estado_valor": estado_valor,
            "archivo_url": archivo.archivo.url if archivo and archivo.archivo else None,
            "numero_gde": archivo.numero_gde if archivo else None,
            "observaciones": archivo.observaciones if archivo else None,
            "es_personalizado": False,
            "row_id": row_id,
            "observaciones": archivo.observaciones if archivo else None,
        }

    @staticmethod
    def serialize_documento_personalizado(archivo):

        estado_display, estado_valor = AdmisionService._estado_display_y_valor(
            archivo.estado
        )

        return {
            "id": archivo.id,
            "documentacion_id": None,
            "archivo_id": archivo.id,
            "nombre": AdmisionService._archivo_nombre(archivo),
            "obligatorio": False,
            "estado": estado_display,
            "estado_valor": estado_valor,
            "archivo_url": archivo.archivo.url if archivo.archivo else None,
            "numero_gde": archivo.numero_gde,
            "observaciones": archivo.observaciones,
            "es_personalizado": True,
            "row_id": f"custom-{archivo.id}",
        }

    @staticmethod
    def _apply_admisiones_text_search(queryset, query):
        query = (query or "").strip()
        if not query:
            return queryset

        query = query.lower()
        return queryset.filter(
            Q(comedor__nombre__icontains=query)
            | Q(comedor__provincia__nombre__icontains=query)
            | Q(comedor__tipocomedor__nombre__icontains=query)
            | Q(comedor__calle__icontains=query)
            | Q(comedor__numero__icontains=query)
            | Q(comedor__referente__nombre__icontains=query)
            | Q(comedor__referente__apellido__icontains=query)
            | Q(comedor__referente__celular__icontains=query)
        )

    @staticmethod
    def get_admisiones_tecnicos_queryset(user, request_or_query=None):
        if user.is_superuser:
            queryset = Admision.objects.all()
        else:
            from users.services import UserPermissionService

            # Verificar si es coordinador usando servicio centralizado
            is_coordinador, duplas_ids = UserPermissionService.get_coordinador_duplas(
                user
            )

            if is_coordinador and duplas_ids:
                # Coordinador: ver admisiones de comedores de sus duplas asignadas
                queryset = Admision.objects.filter(
                    comedor__dupla_id__in=duplas_ids,
                    comedor__dupla__estado="Activo",
                )
            else:
                # Técnico o Abogado: ver admisiones donde está asignado
                queryset = Admision.objects.filter(
                    Q(comedor__dupla__tecnico=user) | Q(comedor__dupla__abogado=user),
                    comedor__dupla__estado="Activo",
                )

        queryset = queryset.exclude(
            Q(enviado_acompaniamiento=True)
            | Q(enviada_a_archivo=True)
            | Q(activa=False)
        )

        if request_or_query is not None:
            if hasattr(request_or_query, "GET"):
                queryset = ADMISION_ADVANCED_FILTER.filter_queryset(
                    queryset, request_or_query
                )
                queryset = AdmisionService._apply_admisiones_text_search(
                    queryset, request_or_query.GET.get("busqueda", "")
                )
            elif hasattr(request_or_query, "get") and not isinstance(
                request_or_query, str
            ):
                queryset = ADMISION_ADVANCED_FILTER.filter_queryset(
                    queryset, request_or_query
                )
                queryset = AdmisionService._apply_admisiones_text_search(
                    queryset, request_or_query.get("busqueda", "")
                )
            else:
                queryset = AdmisionService._apply_admisiones_text_search(
                    queryset, request_or_query
                )

        distinct_ids = queryset.values_list("id", flat=True).distinct()

        return (
            Admision.objects.filter(id__in=distinct_ids)
            .select_related(
                "comedor",
                "comedor__provincia",
                "comedor__tipocomedor",
                "comedor__referente",
                "estado",
            )
            .order_by("-creado")
        )

    @staticmethod
    def get_admisiones_tecnicos_table_data(admisiones, user):
        table_items = []
        admisiones_ids = set()

        def _format_date(value):
            if not value:
                return "-"
            if isinstance(value, datetime) and timezone.is_aware(value):
                value = timezone.localtime(value)
            return value.strftime("%d/%m/%Y")

        for admision in admisiones:
            if admision.id in admisiones_ids:
                continue
            admisiones_ids.add(admision.id)
            comedor = admision.comedor

            comedor_nombre = comedor.nombre if comedor else "-"
            comedor_link_url = (
                reverse("comedor_detalle", args=[comedor.id]) if comedor else None
            )
            tipocomedor_display = (
                str(comedor.tipocomedor)
                if comedor and getattr(comedor, "tipocomedor", None)
                else "-"
            )
            provincia_display = (
                str(comedor.provincia)
                if comedor and getattr(comedor, "provincia", None)
                else "-"
            )
            convenio_display = (
                f"{admision.convenio_numero}°"
                if admision and admision.convenio_numero is not None
                else "-"
            )

            from django.utils.safestring import mark_safe

            badge_html = ""
            if admision.estado_legales == "A Rectificar":
                badge_html = '<span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">Rectificar</span>'
            elif admision.estado_legales == "Archivado":
                badge_html = '<span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">Archivado</span>'

            actions = [
                {
                    "url": reverse("admisiones_tecnicos_editar", args=[admision.pk]),
                    "type": "warning",
                    "label": mark_safe("Ver" + badge_html),
                    "class": "position-relative",
                }
            ]

            table_items.append(
                {
                    "cells": [
                        # ID Comedor
                        {"content": str(comedor.id) if comedor else "-"},
                        # Tipo
                        {
                            "content": (
                                str(admision.get_tipo_display())
                                if admision.tipo
                                else "-"
                            )
                        },
                        # Nombre
                        {
                            "content": comedor_nombre,
                            "link_url": comedor_link_url,
                            "link_class": "font-weight-bold link-handler",
                            "link_title": "Ver detalles",
                        },
                        # Organización
                        {
                            "content": (
                                comedor.organizacion.nombre
                                if comedor and comedor.organizacion
                                else "-"
                            )
                        },
                        # N° Expediente
                        {
                            "content": (
                                admision.num_expediente
                                if admision and admision.num_expediente
                                else "-"
                            )
                        },
                        # N? Convenio
                        {"content": convenio_display},
                        # Provincia
                        {"content": provincia_display},
                        # Equipo tecnico
                        {
                            "content": (
                                str(comedor.dupla) if comedor and comedor.dupla else "-"
                            )
                        },
                        # Estado
                        {
                            "content": (
                                str(admision.get_estado_admision_display())
                                if admision.estado_admision
                                else "-"
                            )
                        },
                        # Última Modificación
                        {"content": _format_date(admision.modificado)},
                    ],
                    "actions": actions,
                }
            )

        return table_items

    @staticmethod
    def get_admision_update_context(admision, user=None):
        try:
            documentaciones = (
                Documentacion.objects.filter(models.Q(convenios=admision.tipo_convenio))
                .distinct()
                .order_by("orden")
            )

            archivos_subidos = ArchivoAdmision.objects.filter(
                admision=admision
            ).select_related("documentacion")

            archivos_por_documentacion = {
                archivo.documentacion_id: archivo
                for archivo in archivos_subidos
                if archivo.documentacion_id
            }

            documentos_info = []
            obligatorios_totales = 0
            obligatorios_completos = 0

            for documentacion in documentaciones:
                archivo = archivos_por_documentacion.get(documentacion.id)
                doc_serializado = AdmisionService._serialize_documentacion(
                    documentacion, archivo
                )
                documentos_info.append(doc_serializado)

                if documentacion.obligatorio:
                    obligatorios_totales += 1
                    if doc_serializado.get("estado") == "Aceptado":
                        obligatorios_completos += 1

            documentos_personalizados_info = [
                AdmisionService.serialize_documento_personalizado(archivo)
                for archivo in archivos_subidos
                if not archivo.documentacion_id
            ]

            resumen_estados = AdmisionService._resumen_documentos(
                documentos_info, documentos_personalizados_info
            )
            stats = AdmisionService._stats_from_resumen(
                resumen_estados, obligatorios_totales, obligatorios_completos
            )

            comedor = admision.comedor
            convenios = TipoConvenio.objects.exclude(id=4)
            caratular_form = CaratularForm(instance=admision) if admision else None
            form_if_informe_tecnico = (
                IFInformeTecnicoForm(instance=admision) if admision else None
            )
            informe_tecnico = (
                InformeTecnico.objects.filter(admision=admision).order_by("-id").first()
            )
            informes_complementarios = InformeComplementario.objects.filter(
                admision=admision
            )

            # Información para informe complementario
            informe_complementario_pendiente = informes_complementarios.filter(
                estado__in=["rectificar", "borrador"]
            ).first()

            mostrar_informe_complementario = (
                admision.estado_legales == "Informe Complementario Solicitado"
                or (
                    informe_complementario_pendiente
                    and informe_complementario_pendiente.estado == "rectificar"
                )
            )

            observaciones_complementario = None
            if (
                informe_complementario_pendiente
                and informe_complementario_pendiente.observaciones_legales
            ):
                observaciones_complementario = (
                    informe_complementario_pendiente.observaciones_legales
                )
            pdf = InformeTecnicoPDF.objects.filter(admision=admision).first()

            # Determinar botones disponibles basado en el estado de la admisión
            botones_disponibles = AdmisionService._get_botones_disponibles(
                admision, informe_tecnico, mostrar_informe_complementario, user
            )

            puede_editar_convenio_numero = False
            if user:
                puede_editar_convenio_numero = (
                    user.is_superuser
                    or AdmisionService._verificar_permiso_tecnico_dupla(user, comedor)
                )

            return {
                "documentos": documentos_info,
                "documentos_personalizados": documentos_personalizados_info,
                "comedor": comedor,
                "convenios": convenios,
                "caratular_form": caratular_form,
                "form_if_informe_tecnico": form_if_informe_tecnico,
                "informe_tecnico": informe_tecnico,
                "pdf": pdf,
                "informes_complementarios": informes_complementarios,
                "resumen_estados": resumen_estados,
                "obligatorios_totales": obligatorios_totales,
                "obligatorios_completos": obligatorios_completos,
                "stats": stats,
                "mostrar_informe_complementario": mostrar_informe_complementario,
                "observaciones_complementario": observaciones_complementario,
                "observaciones_informe_tecnico_complementario": admision.observaciones_informe_tecnico_complementario,
                "botones_disponibles": botones_disponibles,
                "puede_editar_convenio_numero": puede_editar_convenio_numero,
            }

        except Exception:

            logger.exception(
                "Error en get_admision_update_context",
                extra={"admision_pk": admision.pk},
            )

            return {}

    @staticmethod
    def procesar_post_update(request, admision):

        try:

            if "mandarLegales" in request.POST:

                if AdmisionService.marcar_como_enviado_a_legales(
                    admision, request.user
                ):

                    # Actualizar estado de admisión
                    AdmisionService.actualizar_estado_admision(
                        admision, "enviar_a_legales"
                    )

                    return True, "La admisión fue enviada a legales correctamente."

                return False, "La admisión ya estaba marcada como enviada a legales."

            if "btnIFInformeTecnico" in request.POST:

                success, message = AdmisionService.guardar_if_informe_tecnico(
                    request, admision
                )

                if success:
                    # Actualizar estado cuando se carga el IF
                    AdmisionService.actualizar_estado_admision(
                        admision, "cargar_if_informe_tecnico"
                    )

                return success, message

            if "btnDisponibilizarAcomp" in request.POST:

                if AdmisionService.marcar_como_enviado_a_acompaniamiento(
                    admision, request.user
                ):

                    # Actualizar estado de admisión
                    AdmisionService.actualizar_estado_admision(
                        admision, "enviar_a_acompaniamiento"
                    )

                    return True, "Se envió a Acompañamiento correctamente."

                return False, "Error al enviar a Acompañamiento."

            if "btnRectificarDocumentacion" in request.POST:

                if AdmisionService.marcar_como_documentacion_rectificada(
                    admision, request.user
                ):

                    return True, "Se rectificó la documentación."

                return False, "Error al querer realizar la rectificación."

            if "btnCaratulacion" in request.POST:

                form = CaratularForm(request.POST, instance=admision)

                if form.is_valid():

                    form.save()

                    # Actualizar estado cuando se carga el expediente
                    AdmisionService.actualizar_estado_admision(
                        admision, "cargar_expediente"
                    )

                    # Refrescar la instancia desde la base de datos
                    admision.refresh_from_db()

                    return True, "Caratulación del expediente guardado correctamente."

                return False, "Error al guardar la caratulación."

            if "tipo_convenio" in request.POST:

                if AdmisionService.update_convenio(
                    admision, request.POST.get("tipo_convenio")
                ):

                    return True, "Tipo de convenio actualizado correctamente."

            return None, None

        except Exception:

            logger.exception(
                "Error en procesar_post_update",
                extra={"admision_pk": admision.pk},
            )

            return None, "Error inesperado."

    @staticmethod
    def update_convenio(admision, nuevo_convenio_id):

        try:

            if not nuevo_convenio_id:

                return False

            nuevo_convenio = TipoConvenio.objects.get(pk=nuevo_convenio_id)

            admision.tipo_convenio = nuevo_convenio
            admision.estado_id = 1

            admision.save()

            # Actualizar estado de admisión
            AdmisionService.actualizar_estado_admision(admision, "seleccionar_convenio")

            ArchivoAdmision.objects.filter(admision=admision).delete()

            return True

        except Exception:

            logger.exception(
                "Error en update_convenio",
                extra={
                    "admision_pk": admision.pk,
                    "nuevo_convenio_id": nuevo_convenio_id,
                },
            )

            return False

    @staticmethod
    def handle_file_upload(admision_id, documentacion_id, archivo, usuario=None):

        try:

            admision = get_object_or_404(Admision, pk=admision_id)

            documentacion = get_object_or_404(Documentacion, pk=documentacion_id)

            defaults = {
                "archivo": archivo,
                "estado": "Documento adjunto",
                "nombre_personalizado": None,
            }
            if usuario and usuario.is_authenticated:
                defaults["modificado_por"] = usuario

            archivo_admision, created = ArchivoAdmision.objects.update_or_create(
                admision=admision,
                documentacion=documentacion,
                defaults=defaults,
            )
            if created and usuario and usuario.is_authenticated:
                archivo_admision.creado_por = usuario
                archivo_admision.save(update_fields=["creado_por"])

            # Actualizar estado de admisión solo si es la primera vez que se carga un documento
            # y el estado actual permite la transición
            if created and admision.estado_admision == "convenio_seleccionado":
                AdmisionService.actualizar_estado_admision(admision, "cargar_documento")
                # Forzar actualización del estado_mostrar
                admision.save()

            return archivo_admision, created

        except Exception:

            logger.exception(
                "Error en handle_file_upload",
                extra={
                    "admision_id": admision_id,
                    "documentacion_id": documentacion_id,
                },
            )

            return None, False

    @staticmethod
    def crear_documento_personalizado(admision_id, nombre, archivo, usuario):

        try:

            nombre = (nombre or "").strip()

            if not nombre:

                return None, "Debe indicar un nombre para el documento."

            nombre = nombre[:255]

            if not archivo:

                return None, "Debe adjuntar un archivo."

            admision = get_object_or_404(Admision, pk=admision_id)

            if not usuario.is_superuser:

                comedor = admision.comedor

                if not comedor or not AdmisionService._verificar_permiso_dupla(
                    usuario, comedor
                ):

                    return None, "Sin permisos para modificar esta admision."

            with transaction.atomic():

                archivo_admision = ArchivoAdmision.objects.create(
                    admision=admision,
                    documentacion=None,
                    nombre_personalizado=nombre,
                    archivo=archivo,
                    estado="Documento adjunto",
                    creado_por=(
                        usuario if usuario and usuario.is_authenticated else None
                    ),
                    modificado_por=(
                        usuario if usuario and usuario.is_authenticated else None
                    ),
                )

            return archivo_admision, None

        except Exception:

            logger.exception(
                "Error en crear_documento_personalizado",
                extra={"admision_id": admision_id, "nombre": nombre},
            )

            return None, "No se pudo guardar el documento."

    @staticmethod
    def delete_admision_file(archivo):

        try:

            documentacion = archivo.documentacion

            if archivo.archivo:

                file_path = os.path.join(settings.MEDIA_ROOT, str(archivo.archivo))

                if os.path.exists(file_path):

                    os.remove(file_path)

            archivo.delete()

            if (
                documentacion
                and not documentacion.convenios.exists()
                and not ArchivoAdmision.objects.filter(
                    documentacion=documentacion
                ).exists()
            ):

                documentacion.delete()

        except Exception:

            logger.exception(
                "Error en delete_admision_file",
                extra={"archivo_pk": getattr(archivo, "pk", None)},
            )

    @staticmethod
    def actualizar_estado_ajax(request):

        try:

            estado = request.POST.get("estado")

            documento_id = request.POST.get("documento_id")

            admision_id = request.POST.get("admision_id")

            if not all([estado, documento_id, admision_id]):

                return {"success": False, "error": "Datos incompletos."}

            admision = get_object_or_404(Admision, pk=admision_id)

            if not request.user.is_superuser:

                comedor = admision.comedor

                if not comedor:

                    return {"success": False, "error": "Admision sin comedor asociado."}

                if not AdmisionService._verificar_permiso_dupla(request.user, comedor):

                    return {
                        "success": False,
                        "error": "Sin permisos para modificar esta admision.",
                    }

            archivo = get_object_or_404(ArchivoAdmision, id=documento_id)

            grupo_usuario = AdmisionService.get_dupla_grupo_por_usuario(request.user)
            observacion = (request.POST.get("observacion", "") or "").strip()

            display_objetivo, estado_canonico = (
                AdmisionService._normalize_estado_display(estado)
            )

            requiere_observacion = (
                display_objetivo.lower() == "rectificar"
                and grupo_usuario == "Abogado Dupla"
            )
            if requiere_observacion and not observacion:
                return {
                    "success": False,
                    "error": "Debe ingresar observaciones para rectificar.",
                }

            exito = AdmisionService.update_estado_archivo(
                archivo,
                estado_canonico,
                observacion if observacion else None,
            )

            if not exito:

                return {"success": False, "error": "No se pudo actualizar el estado."}

            return {
                "success": True,
                "nuevo_estado": display_objetivo,
                "grupo_usuario": grupo_usuario,
                "observaciones": archivo.observaciones,
            }

        except Exception as e:

            logger.exception(
                "Error en actualizar_estado_ajax",
                extra={"admision_id": admision_id, "documento_id": documento_id},
            )

            return {"success": False, "error": str(e)}

    @staticmethod
    def update_estado_archivo(archivo, nuevo_estado, observacion=None):

        try:

            if not archivo:

                return False

            _, estado_normalizado = AdmisionService._normalize_estado_display(
                nuevo_estado
            )
            archivo.estado = estado_normalizado

            if observacion is not None:
                archivo.observaciones = (
                    observacion.strip() if isinstance(observacion, str) else observacion
                )

            archivo.save()

            # Actualizar estados según la acción del usuario
            AdmisionService._actualizar_estados_por_cambio_documento(
                archivo.admision, estado_normalizado
            )

            return True

        except Exception:

            logger.exception(
                "Error en update_estado_archivo",
                extra={
                    "archivo_pk": getattr(archivo, "pk", None),
                    "nuevo_estado": nuevo_estado,
                },
            )

            return False

    @staticmethod
    def verificar_estado_admision(admision):

        try:

            archivos = ArchivoAdmision.objects.filter(admision=admision).only("estado")

            if admision.estado_id != 3:
                # Verificar que todos los documentos obligatorios estén aceptados
                if AdmisionService._todos_obligatorios_aceptados(admision):
                    if admision.estado_id != 2:
                        admision.estado_id = 2
                        admision.save()

                        # Actualizar estado de admisión cuando toda la documentación obligatoria está aprobada
                        AdmisionService.actualizar_estado_admision(
                            admision, "aprobar_documentacion"
                        )

        except Exception:

            logger.exception(
                "Error en verificar_estado_admision",
                extra={"admision_pk": getattr(admision, "pk", None)},
            )

    @staticmethod
    def get_dupla_grupo_por_usuario(user):

        try:

            if user.groups.filter(name="Abogado Dupla").exists():

                return "Abogado Dupla"

            elif user.groups.filter(name="Tecnico Comedor").exists():

                return "Tecnico Comedor"

            else:

                return "Otro"

        except Exception:

            logger.exception(
                "Error en get_dupla_grupo_por_usuario",
                extra={"user_pk": getattr(user, "pk", None)},
            )

            return "Otro"

    @staticmethod
    def get_admision(admision_id):

        try:

            return get_object_or_404(Admision, pk=admision_id)

        except Exception:

            logger.exception(
                "Error en get_admision",
                extra={"admision_id": admision_id},
            )

            return None

    @staticmethod
    def marcar_como_enviado_a_legales(admision, usuario=None):

        try:

            if not admision.enviado_legales:

                admision.enviado_legales = True
                admision.estado_legales = "Enviado a Legales"
                admision.save()

                # Actualizar estado de admisión
                AdmisionService.actualizar_estado_admision(admision, "enviar_a_legales")

                return True

            return False

        except Exception:

            logger.exception(
                "Error en marcar_como_enviado_a_legales",
                extra={"admision_pk": admision.pk},
            )

            return False

    @staticmethod
    def guardar_if_informe_tecnico(request, admision):

        try:

            form = IFInformeTecnicoForm(request.POST, instance=admision)

            if form.is_valid():

                form.save()

                return True, "Número IF del Informe Técnico guardado correctamente."

            return False, "Error en el formulario. Verifique los datos."

        except Exception:

            logger.exception(
                "Error en guardar_if_informe_tecnico",
                extra={"admision_pk": admision.pk},
            )

            return False, "Error al guardar el número IF del Informe Técnico."

    @staticmethod
    def marcar_como_enviado_a_acompaniamiento(admision, usuario=None):

        try:

            if not admision.enviado_acompaniamiento:

                admision.enviado_acompaniamiento = True
                admision.estado_legales = "Acompañamiento Iniciado"
                admision.save()

                return True

            return False

        except Exception:

            logger.exception(
                "Error en marcar_como_enviado_a_acompaniamiento",
                extra={"admision_pk": admision.pk},
            )

            return False

    @staticmethod
    def marcar_como_documentacion_rectificada(admision, usuario=None):

        try:

            cambios = False

            if not admision.enviado_legales:

                admision.enviado_legales = True

                cambios = True

            if admision.estado_id != 2:

                admision.estado_id = 2

                cambios = True

            if admision.estado_legales != "Rectificado":

                admision.estado_legales = "Rectificado"

                cambios = True

            if admision.observaciones:

                admision.observaciones = None

                cambios = True

            if cambios:

                admision.save()

                return True

            return False

        except Exception:

            logger.exception(
                "Error en marcar_como_documentacion_rectificada",
                extra={"admision_pk": admision.pk},
            )

            return False

    @staticmethod
    def comenzar_acompanamiento(admision_id):

        try:

            admision = get_object_or_404(Admision, pk=admision_id)

            estado_admitido = EstadoAdmision.objects.get(
                nombre="Admitido - pendiente ejecución"
            )

            admision.estado = estado_admitido

            admision.save()

            AcompanamientoService.importar_datos_desde_admision(admision.comedor)

            return admision

        except Exception:

            logger.exception(
                "Error en comenzar_acompanamiento",
                extra={"admision_id": admision_id},
            )

            return None

    @staticmethod
    def get_admision_context(admision_id):

        try:

            admision = get_object_or_404(Admision, id=admision_id)

            return {"admision": admision}

        except Exception:

            logger.exception(
                "Error en get_admision_context",
                extra={"admision_id": admision_id},
            )

            return {}

    @staticmethod
    def get_admision_create_context(comedor_id):
        try:
            from comedores.models import Comedor

            comedor = get_object_or_404(Comedor, id=comedor_id)
            convenios = TipoConvenio.objects.exclude(id=4)

            return {
                "comedor": comedor,
                "convenios": convenios,
            }
        except Exception:
            logger.exception(
                "Error en get_admision_create_context",
                extra={"comedor_id": comedor_id},
            )
            return {}

    @staticmethod
    def create_admision(comedor_id, tipo_convenio_id):
        try:
            from comedores.models import Comedor

            comedor = get_object_or_404(Comedor, id=comedor_id)
            tipo_convenio = get_object_or_404(TipoConvenio, id=tipo_convenio_id)
            estado_inicial = EstadoAdmision.objects.first()

            admision = Admision.objects.create(
                comedor=comedor,
                tipo_convenio=tipo_convenio,
                estado=estado_inicial,
                tipo="incorporacion",
                estado_admision="convenio_seleccionado",
            )

            return admision
        except Exception:
            logger.exception(
                "Error en create_admision",
                extra={"comedor_id": comedor_id, "tipo_convenio_id": tipo_convenio_id},
            )
            return None

    @staticmethod
    def get_admision_instance(admision_id):

        try:

            return get_object_or_404(Admision, id=admision_id)

        except Exception:

            logger.exception(
                "Error en get_admision_instance",
                extra={"admision_id": admision_id},
            )

            return None

    @staticmethod
    def generar_documento_admision(admision, template_name="admision_template.docx"):
        """Genera documento DOCX de admisión usando template"""
        try:
            context = TextFormatterService.preparar_contexto_admision(admision)
            docx_buffer = DocumentTemplateService.generar_docx(template_name, context)

            if docx_buffer:
                filename = f"admision_{admision.id}_{admision.comedor.nombre.replace(' ', '_')}.docx"
                return ContentFile(docx_buffer.getvalue(), name=filename)

            return None
        except Exception:
            logger.exception(
                "Error en generar_documento_admision",
                extra={"admision_id": admision.id, "template": template_name},
            )
            return None

    @staticmethod
    def actualizar_numero_gde_ajax(request):
        """



        Actualiza el número GDE de un documento de admisión vía AJAX.



        Esta función maneja las peticiones AJAX para actualizar el campo numero_gde



        de un documento (ArchivoAdmision). Incluye validaciones de:



        - Estado del documento (debe estar "Aceptado")



        - Permisos del usuario (superuser o técnico de la dupla asignada)



        Args:



            request: HttpRequest con datos POST que debe contener:



                - documento_id: ID del ArchivoAdmision a actualizar



                - numero_gde: Nuevo valor para el número GDE (opcional)



        Returns:



            dict: Respuesta JSON con:



                - success (bool): True si la operación fue exitosa



                - numero_gde (str|None): Valor actualizado (si success=True)



                - valor_anterior (str|None): Valor previo (si success=True)



                - error (str): Mensaje de error (si success=False)



        Raises:



            Http404: Si el documento no existe



            Exception: Errores inesperados loggeados automáticamente



        """

        try:

            documento_id = request.POST.get("documento_id")

            numero_gde = request.POST.get("numero_gde", "").strip()

            if not documento_id:

                return {"success": False, "error": "ID de documento requerido."}

            archivo = get_object_or_404(ArchivoAdmision, id=documento_id)

            if archivo.estado != "Aceptado":

                return {
                    "success": False,
                    "error": "Solo se puede actualizar el número GDE en documentos aceptados.",
                }

            if not (
                request.user.is_superuser
                or AdmisionService._verificar_permiso_dupla(
                    request.user, archivo.admision.comedor
                )
            ):

                return {
                    "success": False,
                    "error": "No tiene permisos para editar este documento.",
                }

            valor_anterior = archivo.numero_gde

            archivo.numero_gde = numero_gde if numero_gde else None

            archivo.save()

            logger.info(
                f"Número GDE actualizado: documento_id={documento_id}, "
                f"valor_anterior='{valor_anterior}', valor_nuevo='{numero_gde}'"
            )

            return {
                "success": True,
                "numero_gde": archivo.numero_gde,
                "valor_anterior": valor_anterior,
            }

        except Exception as e:

            logger.exception(
                "Error en actualizar_numero_gde_ajax",
                extra={"documento_id": documento_id, "numero_gde": numero_gde},
            )

            return {"success": False, "error": str(e)}

    @staticmethod
    def actualizar_convenio_numero_ajax(request):
        """
        Actualiza el numero de convenio de una admision via AJAX.
        """
        try:
            admision_id = request.POST.get("admision_id")
            convenio_numero_raw = request.POST.get("convenio_numero", "").strip()

            if not admision_id:
                return {"success": False, "error": "ID de admision requerido."}

            admision = get_object_or_404(Admision, id=admision_id)

            if not (
                request.user.is_superuser
                or AdmisionService._verificar_permiso_tecnico_dupla(
                    request.user, admision.comedor
                )
            ):
                return {
                    "success": False,
                    "error": "No tiene permisos para editar esta admision.",
                }

            if convenio_numero_raw == "":
                nuevo_valor = None
            else:
                try:
                    nuevo_valor = int(convenio_numero_raw)
                except ValueError:
                    return {
                        "success": False,
                        "error": "Debe ingresar un numero valido.",
                    }
                if nuevo_valor < 0:
                    return {
                        "success": False,
                        "error": "El numero de convenio no puede ser negativo.",
                    }

            valor_anterior = admision.convenio_numero
            admision.convenio_numero = nuevo_valor
            admision.save(update_fields=["convenio_numero"])

            logger.info(
                "Numero de convenio actualizado: admision_id=%s, valor_anterior=%s, valor_nuevo=%s",
                admision_id,
                valor_anterior,
                nuevo_valor,
            )

            return {
                "success": True,
                "convenio_numero": admision.convenio_numero,
                "valor_anterior": valor_anterior,
            }

        except Exception as exc:
            logger.exception(
                "Error en actualizar_convenio_numero_ajax",
                extra={"admision_id": admision_id},
            )
            return {"success": False, "error": str(exc)}

    @staticmethod
    def _verificar_permiso_tecnico_dupla(user, comedor):
        """Verifica que el usuario sea técnico de la dupla asignada al comedor"""

        try:

            return (
                user.groups.filter(name="Tecnico Comedor").exists()
                and comedor.dupla
                and comedor.dupla.tecnico.filter(id=user.id).exists()
                and comedor.dupla.estado == "Activo"
            )

        except Exception:

            logger.exception(
                "Error en _verificar_permiso_tecnico_dupla",
                extra={
                    "user_id": getattr(user, "id", None),
                    "comedor_id": getattr(comedor, "id", None),
                },
            )

            return False

    @staticmethod
    def _verificar_permiso_dupla(user, comedor):
        """Verifica que el usuario sea técnico o abogado de la dupla asignada al comedor"""

        try:

            if not comedor or not hasattr(comedor, "dupla") or not comedor.dupla:

                return False

            dupla = comedor.dupla

            if dupla.estado != "Activo":

                return False

            if user == dupla.abogado:

                return True

            if dupla.tecnico.filter(id=user.id).exists():

                return True

            return False

        except Exception:

            logger.exception(
                "Error en _verificar_permiso_dupla",
                extra={
                    "user_id": getattr(user, "id", None),
                    "comedor_id": getattr(comedor, "id", None),
                },
            )

            return False

    @staticmethod
    def _get_botones_disponibles(
        admision, informe_tecnico, mostrar_informe_complementario, user=None
    ):
        """Determina qué botones deben estar disponibles según el estado de la admisión y el usuario"""
        botones = []

        # Determinar grupo del usuario
        es_tecnico = user and user.groups.filter(name="Tecnico Comedor").exists()
        es_abogado = user and user.groups.filter(name="Abogado Dupla").exists()

        # Botón para comenzar acompañamiento
        if admision.numero_disposicion and not admision.enviado_acompaniamiento:
            botones.append("comenzar_acompaniamiento")

        # Botón para rectificar documentación
        if admision.estado_legales == "A Rectificar":
            botones.append("rectificar_documentacion")

        # Botón para caratular expediente (solo técnicos)
        if (
            es_tecnico
            and admision.estado_admision == "documentacion_aprobada"
            and not admision.num_expediente
        ):
            botones.append("caratular_expediente")

        # Botones para crear/editar informe técnico (solo técnicos)
        if es_tecnico and admision.num_expediente:
            if admision.estado_admision == "expediente_cargado" and not informe_tecnico:
                botones.append("crear_informe_tecnico")
            elif (
                admision.estado_admision == "informe_tecnico_en_proceso"
                and informe_tecnico
                and informe_tecnico.estado in ["Iniciado", "Para revision"]
                and informe_tecnico.estado_formulario == "borrador"
            ):
                botones.append("editar_informe_tecnico")
            elif informe_tecnico and informe_tecnico.estado == "A subsanar":
                botones.append("editar_informe_tecnico")
            elif (
                admision.estado_admision == "informe_tecnico_finalizado"
                and informe_tecnico
                and informe_tecnico.estado == "Docx generado"
            ):
                botones.append("revisar_informe_tecnico")

        # Botón IF Informe Técnico cuando está aprobado (solo técnicos)
        if (
            es_tecnico
            and admision.estado_admision == "informe_tecnico_aprobado"
            and not admision.numero_if_tecnico
        ):
            botones.append("if_informe_tecnico")

        # Botón para derivar a legales cuando el IF está cargado (solo técnicos)
        if (
            es_tecnico
            and admision.estado_admision == "if_informe_tecnico_cargado"
            and not admision.enviado_legales
        ):
            botones.append("mandar_a_legales")

        # Informe técnico validado - informe complementario
        if (
            es_tecnico
            and informe_tecnico
            and informe_tecnico.estado == "Validado"
            and mostrar_informe_complementario
        ):
            botones.append("informe_tecnico_complementario")

        # Botón para ver informe técnico (abogados solo cuando el DOCX editado está subido)
        if (
            es_abogado
            and informe_tecnico
            and admision.estado_admision == "informe_tecnico_docx_editado"
            and informe_tecnico.estado == "Docx editado"
        ):
            botones.append("ver_informe_tecnico")

        return botones

    @staticmethod
    def actualizar_estado_admision(admision, accion):
        """Actualiza el estado_admision basado en la acción realizada"""
        try:
            estado_actual = admision.estado_admision
            nuevo_estado = None

            # Mapeo de acciones a nuevos estados
            transiciones = {
                "seleccionar_convenio": "convenio_seleccionado",
                "cargar_documento": "documentacion_en_proceso",
                "finalizar_documentacion": "documentacion_finalizada",
                "aprobar_documentacion": "documentacion_aprobada",
                "rectificar_documento": "documentacion_en_proceso",
                "cargar_expediente": "expediente_cargado",
                "iniciar_informe_tecnico": "informe_tecnico_en_proceso",
                "finalizar_informe_tecnico": "informe_tecnico_finalizado",
                "enviar_informe_revision": "informe_tecnico_docx_editado",
                "subsanar_informe": "informe_tecnico_en_subsanacion",
                "aprobar_informe_tecnico": "informe_tecnico_aprobado",
                "cargar_if_informe_tecnico": "if_informe_tecnico_cargado",
                "enviar_a_legales": "enviado_a_legales",
                "enviar_a_acompaniamiento": "enviado_a_acompaniamiento",
            }

            nuevo_estado = transiciones.get(accion)

            if nuevo_estado and nuevo_estado != estado_actual:
                admision.estado_admision = nuevo_estado
                admision.save()
                return True

            return False

        except Exception:
            logger.exception(
                "Error en actualizar_estado_admision",
                extra={"admision_pk": admision.pk, "accion": accion},
            )
            return False

    @staticmethod
    def _todos_obligatorios_aceptados(admision):
        """Verifica que todos los documentos obligatorios del tipo de convenio estén aceptados"""
        try:
            # Obtener documentos obligatorios para el tipo de convenio
            documentos_obligatorios = Documentacion.objects.filter(
                convenios=admision.tipo_convenio, obligatorio=True
            )

            # Verificar que cada documento obligatorio tenga un archivo aceptado
            for doc_obligatorio in documentos_obligatorios:
                archivo = ArchivoAdmision.objects.filter(
                    admision=admision, documentacion=doc_obligatorio, estado="Aceptado"
                ).first()

                if not archivo:
                    return False

            return True

        except Exception:
            logger.exception(
                "Error en _todos_obligatorios_aceptados",
                extra={"admision_pk": admision.pk},
            )
            return False

    @staticmethod
    def _actualizar_estados_por_cambio_documento(admision, estado_documento):
        """Actualiza estados de admisión basado en cambios de documentos"""
        try:
            # Si un documento se marca como "Rectificar", solo retroceder si es un documento obligatorio
            if estado_documento == "Rectificar":
                if admision.estado_admision in [
                    "documentacion_finalizada",
                    "documentacion_aprobada",
                ]:
                    # Solo retroceder si hay documentos obligatorios que necesitan rectificación
                    if not AdmisionService._todos_obligatorios_aceptados(admision):
                        admision.estado_admision = "documentacion_en_proceso"
                        admision.save()  # Save completo para actualizar estado_mostrar
                return

            # No avanzar estados si ya está en documentacion_aprobada o más adelante
            # Esto evita que documentos adicionales hagan retroceder el estado
            if admision.estado_admision in [
                "documentacion_aprobada",
                "expediente_cargado",
                "informe_tecnico_en_proceso",
                "informe_tecnico_finalizado",
                "informe_tecnico_docx_editado",
                "informe_tecnico_en_revision",
                "informe_tecnico_en_subsanacion",
                "informe_tecnico_aprobado",
                "if_informe_tecnico_cargado",
                "enviado_a_legales",
                "enviado_a_acompaniamiento",
            ]:
                return

            # Verificar si todos los obligatorios tienen archivos (no necesariamente aceptados)
            if AdmisionService._todos_obligatorios_tienen_archivos(admision):
                if admision.estado_admision == "documentacion_en_proceso":
                    admision.estado_admision = "documentacion_finalizada"
                    admision.save()  # Save completo para actualizar estado_mostrar

            # Verificar si todos los obligatorios están aceptados
            if AdmisionService._todos_obligatorios_aceptados(admision):
                if admision.estado_admision == "documentacion_finalizada":
                    admision.estado_admision = "documentacion_aprobada"
                    # También actualizar el estado principal a "Finalizada"
                    if admision.estado_id != 2:
                        admision.estado_id = 2
                    admision.save()  # Save completo para actualizar estado_mostrar

        except Exception:
            logger.exception(
                "Error en _actualizar_estados_por_cambio_documento",
                extra={
                    "admision_pk": admision.pk,
                    "estado_documento": estado_documento,
                },
            )

    @staticmethod
    def _todos_obligatorios_tienen_archivos(admision):
        """Verifica que todos los documentos obligatorios tengan archivos cargados"""
        try:
            documentos_obligatorios = Documentacion.objects.filter(
                convenios=admision.tipo_convenio, obligatorio=True
            )

            for doc_obligatorio in documentos_obligatorios:
                archivo = ArchivoAdmision.objects.filter(
                    admision=admision, documentacion=doc_obligatorio
                ).first()

                if not archivo or not archivo.archivo:
                    return False

            return True

        except Exception:
            logger.exception(
                "Error en _todos_obligatorios_tienen_archivos",
                extra={"admision_pk": admision.pk},
            )
            return False
