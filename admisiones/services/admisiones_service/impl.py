import os
import re
import unicodedata
from datetime import datetime
from django.conf import settings
from django.db import models
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
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
    NumeroGdeOrganizacion,
    AdmisionDocOrgSnapshot,
)
from admisiones.forms.admisiones_forms import (
    CaratularForm,
    IFInformeTecnicoForm,
)
from acompanamientos.acompanamiento_service import AcompanamientoService
from ..docx_service import DocumentTemplateService, TextFormatterService
from core.services.advanced_filters import AdvancedFilterEngine
from iam.services import user_has_any_permission_codes, user_has_permission_code
from admisiones.services.admisiones_filter_config import (
    FIELD_MAP as ADMISION_FILTER_MAP,
    FIELD_TYPES as ADMISION_FIELD_TYPES,
    TEXT_OPS as ADMISION_TEXT_OPS,
    NUM_OPS as ADMISION_NUM_OPS,
    DATE_OPS as ADMISION_DATE_OPS,
    CHOICE_OPS as ADMISION_CHOICE_OPS,
)
from comedores.utils import comedor_usa_admision_para_nomina
from organizaciones.models import ArchivoOrganizacion, DocumentacionOrganizacion

from django.db.models import Prefetch, Q
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
    TIPO_ENTIDAD_A_CONVENIO = {
        "personeria juridica": "personeria juridica",
        "personeria juridica eclesiastica": "personeria juridica eclesiastica",
        "asociacion de hecho": "organizacion base",
    }

    ESTADOS_BLOQUEO_ELIMINACION_DOCUMENTAL = (
        "informe_tecnico_finalizado",
        "informe_tecnico_docx_editado",
        "informe_tecnico_en_revision",
        "informe_tecnico_en_subsanacion",
        "informe_tecnico_aprobado",
        "if_informe_tecnico_cargado",
        "enviado_a_legales",
        "enviado_a_acompaniamiento",
        "descartado",
        "inactivada",
    )
    ESTADOS_BLOQUEO_AVANCE_DOCUMENTAL = (
        "documentacion_aprobada",
        "expediente_cargado",
        "informe_tecnico_en_proceso",
        *ESTADOS_BLOQUEO_ELIMINACION_DOCUMENTAL,
    )
    ESTADOS_DOCUMENTACION_ORGANIZACIONAL_CONGELADA = (
        "informe_tecnico_finalizado",
        "informe_tecnico_docx_editado",
        "informe_tecnico_en_revision",
        "informe_tecnico_en_subsanacion",
        "informe_tecnico_aprobado",
        "if_informe_tecnico_cargado",
        "enviado_a_legales",
        "enviado_a_acompaniamiento",
    )
    CATEGORIA_ORGANIZACIONAL_POR_TIPO_CONVENIO = {
        1: DocumentacionOrganizacion.CATEGORIA_BASE,
        2: DocumentacionOrganizacion.CATEGORIA_ECLESIASTICA,
        3: DocumentacionOrganizacion.CATEGORIA_PERSONERIA,
    }
    ALIAS_DOCUMENTACION_ORGANIZACIONAL = {
        DocumentacionOrganizacion.CATEGORIA_PERSONERIA: {
            "acta constitutiva": "acta constitutiva de la organizacion",
            "estatuto": "estatuto social vigente",
            "reso personeria juridica": "resolucion de otorgamiento de la personeria juridica",
            "resolucion personeria juridica": "resolucion de otorgamiento de la personeria juridica",
            "acta de designacion de autoridades": "acta de designacion de autoridades vigentes",
            "dni presidente": "dni del presidente",
            "dni tesorero": "dni del tesorero",
            "dni secretario": "dni del secretario",
            # "Acta de Solicitud de Subsidio" se gestiona como documento nativo
            # de la Admision (issue #1799 Req 2); ya no se materializa desde el
            # legajo de la Organizacion.
            "constancia de arca": "constancia de inscripcion ante arca",
            "preinscripcion renacom": "constancia de preinscripcion en renacom",
            "validacion renacom": "constancia de validacion en renacom",
            "inscripcion renacom": "constancia de inscripcion definitiva en renacom",
        },
        DocumentacionOrganizacion.CATEGORIA_ECLESIASTICA: {
            "designacion autoridad maxima": "acta o documento de designacion de la autoridad maxima",
            "certificado de culto": "certificado de culto vigente",
            "dni obispo": "dni del obispo o autoridad eclesiastica",
            "constancia de arca": "constancia de inscripcion ante arca",
            "preinscripcion renacom": "constancia de preinscripcion en renacom",
            "validacion renacom": "constancia de validacion en renacom",
            "inscripcion renacom": "constancia de inscripcion definitiva en renacom",
            "decreto de reconocimiento del estado nacional": "decreto de reconocimiento del estado nacional",
            "apoderado": "documento de designacion de apoderado",
            "dni apoderado": "dni del apoderado",
            "estatuto": "estatuto institucional",
            "conformacion de la comision diocesana": "acta de conformacion de la comision diocesana",
            "autorizacion para gestionar": "autorizacion para gestionar",
        },
        DocumentacionOrganizacion.CATEGORIA_BASE: {
            "acta de asamblea": "acta de asamblea constitutiva",
            "dni responsable 1": "dni del responsable 1",
            "dni responsable 2": "dni del responsable 2",
            "acta designacion aval 1 designacion de cargo aval 1 persona fisica": "acta designacion aval 1 designacion de cargo aval 1 persona fisica o juridica",
            "dni autoridad maxima aval 1 dni aval 1 persona fisica": "dni de la autoridad maxima del aval 1 dni del aval 1 segun corresponda",
            "acta designacion aval 2 designacion de cargo aval 2 persona fisica": "acta designacion aval 2 designacion de cargo aval 2 persona fisica o juridica",
            "dni autoridad maxima aval 2 dni aval 2 persona fisica": "dni de la autoridad maxima del aval 2 dni del aval 2 segun corresponda",
            "nota aval 1": "nota de aval emitida por el aval 1",
            "nota aval 2": "nota de aval emitida por el aval 2",
            "acta constitutiva aval 1": "acta constitutiva del aval 1",
            "estatuto aval 1": "estatuto del aval 1",
            "reso personeria juridica aval 1": "resolucion de personeria juridica del aval 1",
            "acta constitutiva aval 2": "acta constitutiva del aval 2",
            "estatuto aval 2": "estatuto del aval 2",
            "reso personeria juridica aval 2": "resolucion de personeria juridica del aval 2",
            "preinscripcion renacom": "constancia de preinscripcion en renacom",
            "validacion renacom": "constancia de validacion en renacom",
            "inscripcion renacom": "constancia de inscripcion definitiva en renacom",
        },
    }

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
    def _normalizar_nombre_documental(nombre):
        texto = unicodedata.normalize("NFKD", str(nombre or ""))
        texto = texto.encode("ascii", "ignore").decode("ascii").lower()
        return re.sub(r"[^a-z0-9]+", " ", texto).strip()

    @staticmethod
    def _categoria_organizacional_admision(admision):
        return AdmisionService.CATEGORIA_ORGANIZACIONAL_POR_TIPO_CONVENIO.get(
            getattr(admision, "tipo_convenio_id", None)
        )

    @staticmethod
    def _org_doc_key_desde_documentacion_admision(documentacion, categoria):
        if not categoria or not documentacion:
            return None
        nombre_normalizado = AdmisionService._normalizar_nombre_documental(
            documentacion.nombre
        )
        return AdmisionService.ALIAS_DOCUMENTACION_ORGANIZACIONAL.get(
            categoria, {}
        ).get(nombre_normalizado)

    @staticmethod
    def _get_archivos_organizacion_vigentes(admision, categoria):
        organizacion = getattr(getattr(admision, "comedor", None), "organizacion", None)
        if not organizacion or not categoria:
            return {}

        archivos = (
            ArchivoOrganizacion.objects.filter(
                organizacion=organizacion,
                documentacion__categoria=categoria,
            )
            .select_related("documentacion")
            .order_by("documentacion_id", "-creado", "-id")
        )
        vigentes = {}
        for archivo in archivos:
            vigentes.setdefault(archivo.documentacion_id, archivo)
        return vigentes

    @staticmethod
    def _serializar_documentacion_organizacion(
        org_doc,
        archivo=None,
        admision_doc=None,
        numero_gde_admision=None,
    ):
        estado_display, estado_valor = AdmisionService._estado_display_y_valor(
            archivo.estado if archivo else "pendiente"
        )
        return {
            "id": f"org-{org_doc.id}",
            "documentacion_id": admision_doc.id if admision_doc else None,
            "archivo_id": None,
            "archivo_organizacion_id": archivo.id if archivo else None,
            "nombre": org_doc.nombre,
            "obligatorio": org_doc.obligatorio,
            "estado": estado_display,
            "estado_valor": estado_valor,
            "archivo_url": archivo.archivo.url if archivo and archivo.archivo else None,
            "numero_gde": numero_gde_admision,
            "fecha_vencimiento": archivo.fecha_vencimiento if archivo else None,
            "observaciones": archivo.observaciones if archivo else None,
            "es_personalizado": False,
            "es_documento_organizacion": True,
            "es_origen_organizacion": True,
            "origen": "organizacion",
            "row_id": f"org-{org_doc.id}",
        }

    @staticmethod
    def _crear_archivo_admision_desde_archivo_organizacion(
        admision, org_doc, archivo_org, documentacion_admision=None
    ):
        numero_gde = AdmisionService._resolver_numero_gde_para_clonado(
            admision, archivo_org
        )
        archivo_admision = ArchivoAdmision.objects.create(
            admision=admision,
            documentacion=documentacion_admision,
            nombre_personalizado=(
                None
                if documentacion_admision
                else (org_doc.nombre if org_doc else archivo_org.nombre_personalizado)
            ),
            archivo=archivo_org.archivo.name,
            estado=archivo_org.estado,
            observaciones=archivo_org.observaciones,
            numero_gde=numero_gde,
            archivo_organizacion_origen=archivo_org,
            creado_por=archivo_org.creado_por,
            modificado_por=archivo_org.modificado_por,
        )
        if numero_gde:
            # El GDE ahora vive en el ArchivoAdmision clonado; el registro
            # en NumeroGdeOrganizacion para esta combinacion deja de ser
            # canonico y se elimina para evitar valores divergentes.
            NumeroGdeOrganizacion.objects.filter(
                admision=admision, archivo_organizacion=archivo_org
            ).delete()
        return archivo_admision

    @staticmethod
    def _resolver_numero_gde_para_clonado(admision, archivo_org):
        """Resuelve el numero_gde a usar al materializar un ArchivoOrganizacion
        como ArchivoAdmision. Prioriza el GDE registrado para esta admision en
        ``NumeroGdeOrganizacion`` (donde el tecnico carga el valor desde la
        admision) y cae al ``ArchivoOrganizacion.numero_gde`` historico como
        fallback.
        """

        numero_admision = (
            NumeroGdeOrganizacion.objects.filter(
                admision=admision, archivo_organizacion=archivo_org
            )
            .values_list("numero_gde", flat=True)
            .first()
        )
        if numero_admision:
            return numero_admision
        return getattr(archivo_org, "numero_gde", None) or None

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
            "es_documento_organizacion": False,
            "es_origen_organizacion": (
                bool(getattr(archivo, "archivo_organizacion_origen_id", None))
                if archivo
                else False
            ),
            "origen": "admision",
        }

    @staticmethod
    def _build_documentos_organizacionales_update_context(
        admision, documentaciones, archivos_por_documentacion
    ):
        categoria = AdmisionService._categoria_organizacional_admision(admision)
        if not categoria:
            return [], set()

        org_docs = list(
            DocumentacionOrganizacion.objects.filter(categoria=categoria).order_by(
                "orden", "id"
            )
        )
        org_docs_por_key = {
            AdmisionService._normalizar_nombre_documental(org_doc.nombre): org_doc
            for org_doc in org_docs
        }
        admision_doc_por_org_key = {}
        ids_documentacion_admision_usados = set()

        for documentacion in documentaciones:
            org_key = AdmisionService._org_doc_key_desde_documentacion_admision(
                documentacion, categoria
            )
            if org_key and org_key in org_docs_por_key:
                admision_doc_por_org_key[org_key] = documentacion
                ids_documentacion_admision_usados.add(documentacion.id)

        archivos_org = AdmisionService._get_archivos_organizacion_vigentes(
            admision, categoria
        )
        numeros_gde_por_archivo_org = (
            AdmisionService._get_numeros_gde_organizacion_por_archivo(
                admision,
                [archivo.id for archivo in archivos_org.values() if archivo],
            )
        )
        documentos = []
        for org_doc in org_docs:
            org_key = AdmisionService._normalizar_nombre_documental(org_doc.nombre)
            admision_doc = admision_doc_por_org_key.get(org_key)
            archivo_org = archivos_org.get(org_doc.id)
            archivo_admision = (
                archivos_por_documentacion.get(admision_doc.id)
                if admision_doc
                else None
            )
            numero_gde_admision = (
                numeros_gde_por_archivo_org.get(archivo_org.id) if archivo_org else None
            )
            if archivo_admision:
                doc_serializado = (
                    AdmisionService._serialize_documentacion(
                        admision_doc, archivo_admision
                    )
                    if admision_doc
                    else AdmisionService.serialize_documento_personalizado(
                        archivo_admision
                    )
                )
                doc_serializado.update(
                    {
                        "nombre": org_doc.nombre,
                        "obligatorio": org_doc.obligatorio,
                        "es_documento_organizacion": True,
                        "origen": "organizacion",
                        "fecha_vencimiento": (
                            archivo_org.fecha_vencimiento if archivo_org else None
                        ),
                        "archivo_organizacion_id": (
                            archivo_org.id if archivo_org else None
                        ),
                    }
                )
                if numero_gde_admision is not None:
                    doc_serializado["numero_gde"] = numero_gde_admision
            else:
                doc_serializado = (
                    AdmisionService._serializar_documentacion_organizacion(
                        org_doc,
                        archivo_org,
                        admision_doc=admision_doc,
                        numero_gde_admision=numero_gde_admision,
                    )
                )
            documentos.append(doc_serializado)

        return documentos, ids_documentacion_admision_usados

    @staticmethod
    def _get_numeros_gde_organizacion_por_archivo(admision, archivo_org_ids):
        if not admision or not archivo_org_ids:
            return {}
        registros = NumeroGdeOrganizacion.objects.filter(
            admision=admision,
            archivo_organizacion_id__in=archivo_org_ids,
        ).values_list("archivo_organizacion_id", "numero_gde")
        return {archivo_id: numero for archivo_id, numero in registros}

    @staticmethod
    def _build_documentos_update_context(
        documentaciones, archivos_subidos, admision=None
    ):
        archivos_por_documentacion = {
            archivo.documentacion_id: archivo
            for archivo in archivos_subidos
            if archivo.documentacion_id
        }

        documentos_info = []
        obligatorios_totales = 0
        obligatorios_completos = 0
        ids_documentacion_admision_usados = set()

        if admision:
            (
                documentos_info,
                ids_documentacion_admision_usados,
            ) = AdmisionService._build_documentos_organizacionales_update_context(
                admision,
                documentaciones,
                archivos_por_documentacion,
            )
            for doc_serializado in documentos_info:
                if doc_serializado.get("obligatorio"):
                    obligatorios_totales += 1
                    if doc_serializado.get("estado") == "Aceptado":
                        obligatorios_completos += 1

        for documentacion in documentaciones:
            if documentacion.id in ids_documentacion_admision_usados:
                continue
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

        return {
            "documentos": documentos_info,
            "documentos_personalizados": documentos_personalizados_info,
            "resumen_estados": resumen_estados,
            "obligatorios_totales": obligatorios_totales,
            "obligatorios_completos": obligatorios_completos,
            "stats": stats,
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
            "es_documento_organizacion": False,
            "origen": "admision",
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
    def _build_informe_complementario_update_context(
        admision, informes_complementarios
    ):
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

        return {
            "mostrar_informe_complementario": mostrar_informe_complementario,
            "observaciones_complementario": observaciones_complementario,
        }

    @staticmethod
    def _puede_editar_convenio_numero_update_context(user, comedor):
        if not user:
            return False
        return user.is_superuser or AdmisionService._verificar_permiso_tecnico_dupla(
            user, comedor
        )

    @staticmethod
    def _puede_editar_num_expediente_update_context(user, admision):
        if not user or not admision or getattr(admision, "enviado_legales", False):
            return False
        return user.is_superuser or AdmisionService._verificar_permiso_tecnico_dupla(
            user, admision.comedor
        )

    @staticmethod
    def _build_objetos_update_context(admision):
        tipo_convenio_precargado = (
            AdmisionService.resolver_tipo_convenio_desde_organizacion(
                getattr(getattr(admision, "comedor", None), "organizacion", None)
            )
            if admision
            else None
        )
        return {
            "comedor": admision.comedor,
            "convenios": TipoConvenio.objects.exclude(id=4),
            "tipo_convenio_precargado": tipo_convenio_precargado,
            "caratular_form": CaratularForm(instance=admision) if admision else None,
            "form_if_informe_tecnico": (
                IFInformeTecnicoForm(instance=admision) if admision else None
            ),
            "informe_tecnico": (
                InformeTecnico.objects.filter(admision=admision).order_by("-id").first()
            ),
            "informes_complementarios": InformeComplementario.objects.filter(
                admision=admision
            ),
            "pdf": InformeTecnicoPDF.objects.filter(admision=admision).first(),
        }

    @staticmethod
    def _build_response_update_context(
        *,
        admision,
        documentos_context,
        objetos_contexto,
        informe_complementario_context,
        botones_disponibles,
        puede_editar_convenio_numero,
        puede_editar_num_expediente,
    ):
        organizacion = getattr(getattr(admision, "comedor", None), "organizacion", None)
        tipo_entidad_actual = getattr(organizacion, "tipo_entidad", None)
        admision_desincronizada = AdmisionService.admision_desincronizada(admision)
        documentacion_desactualizada, documentos_org_modificados = (
            AdmisionService.admision_documentacion_desactualizada(admision)
        )
        mostrar_modal_resync_org = (
            admision_desincronizada or documentacion_desactualizada
        ) and not getattr(admision, "enviada_a_archivo", False)
        return {
            "documentos": documentos_context["documentos"],
            "documentos_personalizados": documentos_context[
                "documentos_personalizados"
            ],
            "comedor": objetos_contexto["comedor"],
            "convenios": objetos_contexto["convenios"],
            "tipo_convenio_precargado": objetos_contexto["tipo_convenio_precargado"],
            "caratular_form": objetos_contexto["caratular_form"],
            "form_if_informe_tecnico": objetos_contexto["form_if_informe_tecnico"],
            "informe_tecnico": objetos_contexto["informe_tecnico"],
            "pdf": objetos_contexto["pdf"],
            "informes_complementarios": objetos_contexto["informes_complementarios"],
            "resumen_estados": documentos_context["resumen_estados"],
            "obligatorios_totales": documentos_context["obligatorios_totales"],
            "obligatorios_completos": documentos_context["obligatorios_completos"],
            "stats": documentos_context["stats"],
            "mostrar_informe_complementario": informe_complementario_context[
                "mostrar_informe_complementario"
            ],
            "observaciones_complementario": informe_complementario_context[
                "observaciones_complementario"
            ],
            "observaciones_informe_tecnico_complementario": admision.observaciones_informe_tecnico_complementario,
            "botones_disponibles": botones_disponibles,
            "puede_editar_convenio_numero": puede_editar_convenio_numero,
            "puede_editar_num_expediente": puede_editar_num_expediente,
            "admision_desincronizada": admision_desincronizada,
            "tipo_entidad_actual_organizacion": tipo_entidad_actual,
            "tipo_entidad_origen_snapshot": getattr(
                admision, "tipo_entidad_origen", None
            ),
            "documentacion_desactualizada": documentacion_desactualizada,
            "documentos_org_modificados": documentos_org_modificados,
            "mostrar_modal_resync_org": mostrar_modal_resync_org,
        }

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
            documentos_context = AdmisionService._build_documentos_update_context(
                documentaciones=documentaciones,
                archivos_subidos=archivos_subidos,
                admision=admision,
            )
            objetos_contexto = AdmisionService._build_objetos_update_context(admision)
            informe_complementario_context = (
                AdmisionService._build_informe_complementario_update_context(
                    admision,
                    objetos_contexto["informes_complementarios"],
                )
            )

            # Determinar botones disponibles basado en el estado de la admisión
            botones_disponibles = AdmisionService._get_botones_disponibles(
                admision,
                objetos_contexto["informe_tecnico"],
                informe_complementario_context["mostrar_informe_complementario"],
                user,
            )
            puede_editar_convenio_numero = (
                AdmisionService._puede_editar_convenio_numero_update_context(
                    user, objetos_contexto["comedor"]
                )
            )
            puede_editar_num_expediente = (
                AdmisionService._puede_editar_num_expediente_update_context(
                    user, admision
                )
            )

            return AdmisionService._build_response_update_context(
                admision=admision,
                documentos_context=documentos_context,
                objetos_contexto=objetos_contexto,
                informe_complementario_context=informe_complementario_context,
                botones_disponibles=botones_disponibles,
                puede_editar_convenio_numero=puede_editar_convenio_numero,
                puede_editar_num_expediente=puede_editar_num_expediente,
            )

        except Exception:

            logger.exception(
                "Error en get_admision_update_context",
                extra={"admision_pk": admision.pk},
            )

            return {}

    @staticmethod
    def _procesar_post_mandar_legales(admision, user):
        if not AdmisionService.marcar_como_enviado_a_legales(admision, user):
            return False, "La admisión ya estaba marcada como enviada a legales."

        AdmisionService.actualizar_estado_admision(admision, "enviar_a_legales")
        return True, "La admisión fue enviada a legales correctamente."

    @staticmethod
    def _procesar_post_if_informe_tecnico(request, admision):
        success, message = AdmisionService.guardar_if_informe_tecnico(request, admision)
        if success:
            AdmisionService.actualizar_estado_admision(
                admision, "cargar_if_informe_tecnico"
            )
        return success, message

    @staticmethod
    def _procesar_post_disponibilizar_acomp(admision, user):
        with transaction.atomic():
            AcompanamientoService.importar_datos_desde_admision(admision)
            if not AdmisionService.marcar_como_enviado_a_acompaniamiento(
                admision, user
            ):
                return False, "Error al enviar a Acompañamiento."
            if not AdmisionService.actualizar_estado_admision(
                admision, "enviar_a_acompaniamiento"
            ):
                raise RuntimeError(
                    "No se pudo actualizar el estado de la admisión a acompañamiento."
                )

        return True, "Se envió a Acompañamiento correctamente."

    @staticmethod
    def _procesar_post_rectificar_documentacion(admision, user):
        if not AdmisionService.marcar_como_documentacion_rectificada(admision, user):
            return False, "Error al querer realizar la rectificación."
        return True, "Se rectificó la documentación."

    @staticmethod
    def _procesar_post_finalizar_carga_documentacion(admision):
        if not AdmisionService.actualizar_estado_admision(
            admision, "finalizar_carga_documentacion"
        ):
            return False, "No se pudo finalizar la carga de documentación."
        return True, "Carga de documentación finalizada correctamente."

    @staticmethod
    def _procesar_post_caratulacion(request, admision):
        if admision.estado_admision != "documentacion_carga_finalizada":
            return (
                False,
                "Debe finalizar la carga de documentación antes de caratular.",
            )

        form = CaratularForm(request.POST, instance=admision)
        if not form.is_valid():
            return False, "Error al guardar la caratulación."

        form.save()
        AdmisionService.actualizar_estado_admision(admision, "cargar_expediente")
        admision.refresh_from_db()
        return True, "Caratulación del expediente guardado correctamente."

    @staticmethod
    def _dispatch_post_update_action(request, admision):
        actions = (
            (
                "mandarLegales",
                lambda: AdmisionService._procesar_post_mandar_legales(
                    admision, request.user
                ),
            ),
            (
                "btnIFInformeTecnico",
                lambda: AdmisionService._procesar_post_if_informe_tecnico(
                    request, admision
                ),
            ),
            (
                "btnDisponibilizarAcomp",
                lambda: AdmisionService._procesar_post_disponibilizar_acomp(
                    admision, request.user
                ),
            ),
            (
                "btnRectificarDocumentacion",
                lambda: AdmisionService._procesar_post_rectificar_documentacion(
                    admision, request.user
                ),
            ),
            (
                "btnFinalizarCargaDocumentacion",
                lambda: AdmisionService._procesar_post_finalizar_carga_documentacion(
                    admision
                ),
            ),
            (
                "btnCaratulacion",
                lambda: AdmisionService._procesar_post_caratulacion(request, admision),
            ),
            (
                "confirmar_tipo_convenio",
                lambda: AdmisionService._procesar_post_confirmar_tipo_convenio(
                    admision
                ),
            ),
        )
        for key, handler in actions:
            if key in request.POST:
                return handler()
        return None, None

    @staticmethod
    def procesar_post_update(request, admision):
        try:
            return AdmisionService._dispatch_post_update_action(request, admision)
        except Exception:

            logger.exception(
                "Error en procesar_post_update",
                extra={"admision_pk": admision.pk},
            )

            return None, "Error inesperado."

    @staticmethod
    def _aplicar_cambio_convenio_y_reset_documentos(admision, nuevo_convenio):
        admision.tipo_convenio = nuevo_convenio
        admision.estado_id = 1
        admision.save()
        AdmisionService.actualizar_estado_admision(admision, "seleccionar_convenio")
        ArchivoAdmision.objects.filter(admision=admision).delete()

    @staticmethod
    def _asegurar_snapshot_tipo_entidad(admision):
        """Inicializa ``tipo_entidad_origen`` cuando esta vacio adoptando el
        ``tipo_entidad`` actual de la organizacion. Cubre admisiones legacy
        anteriores a la introduccion del snapshot y admisiones creadas por
        flujos que no lo seteaban.
        """

        if getattr(admision, "tipo_entidad_origen_id", None):
            return
        organizacion = getattr(getattr(admision, "comedor", None), "organizacion", None)
        tipo_actual_id = getattr(organizacion, "tipo_entidad_id", None)
        if not tipo_actual_id:
            return
        admision.tipo_entidad_origen_id = tipo_actual_id
        admision.save(update_fields=["tipo_entidad_origen"])

    @staticmethod
    def admision_desincronizada(admision):
        """Indica si el ``tipo_entidad_origen`` snapshotado en la admision
        difiere del ``tipo_entidad`` actual de la organizacion. Si el snapshot
        esta vacio (admisiones legacy) se inicializa con el valor actual y se
        considera sincronizada hasta el proximo cambio.
        """

        organizacion = getattr(getattr(admision, "comedor", None), "organizacion", None)
        if not organizacion:
            return False
        tipo_actual_id = getattr(organizacion, "tipo_entidad_id", None)
        if not tipo_actual_id:
            return False
        AdmisionService._asegurar_snapshot_tipo_entidad(admision)
        snapshot_id = getattr(admision, "tipo_entidad_origen_id", None)
        if not snapshot_id:
            return False
        return tipo_actual_id != snapshot_id

    @staticmethod
    def resync_admision_desde_organizacion(admision):
        """Resetea la admision usando como fuente la organizacion: borra todos
        los ``ArchivoAdmision``, vuelve el estado a ``convenio_seleccionado``,
        ajusta ``tipo_convenio`` segun el nuevo ``tipo_entidad`` y actualiza el
        snapshot."""

        organizacion = getattr(getattr(admision, "comedor", None), "organizacion", None)
        if not organizacion:
            return False, "La admision no tiene organizacion asociada."

        nuevo_convenio = AdmisionService.resolver_tipo_convenio_desde_organizacion(
            organizacion
        )
        if not nuevo_convenio:
            return (
                False,
                "No se pudo resolver el Tipo de Convenio desde el Tipo de Entidad de la organizacion.",
            )

        AdmisionService._aplicar_cambio_convenio_y_reset_documentos(
            admision, nuevo_convenio
        )
        admision.tipo_entidad_origen_id = organizacion.tipo_entidad_id
        admision.save(update_fields=["tipo_entidad_origen"])
        AdmisionService.congelar_documentacion_organizacional(admision)
        AdmisionService.refrescar_snapshot_documentacion_organizacional(admision)
        logger.info(
            "Admision resincronizada desde la organizacion",
            extra={
                "admision_pk": admision.pk,
                "tipo_entidad_id": organizacion.tipo_entidad_id,
            },
        )
        return True, "Admision actualizada desde el Legajo de la Organizacion."

    @staticmethod
    def aceptar_desincronizacion_admision(admision):
        """Mantiene el estado actual de la admision pero actualiza el snapshot
        de ``tipo_entidad_origen`` para que la advertencia desaparezca hasta el
        proximo cambio en la organizacion."""

        organizacion = getattr(getattr(admision, "comedor", None), "organizacion", None)
        if not organizacion:
            return False, "La admision no tiene organizacion asociada."

        admision.tipo_entidad_origen_id = organizacion.tipo_entidad_id
        admision.save(update_fields=["tipo_entidad_origen"])
        AdmisionService.refrescar_snapshot_documentacion_organizacional(admision)
        logger.info(
            "Desincronizacion aceptada en admision",
            extra={
                "admision_pk": admision.pk,
                "tipo_entidad_id": organizacion.tipo_entidad_id,
            },
        )
        return True, "Continuara operando con la informacion actual de la admision."

    @staticmethod
    def actualizar_documentacion_desde_organizacion(admision, user=None):
        """Issue #1799 (feedback punto 1): "Actualizar Informacion desde Legajo
        Organizacion" DIRIGIDO. Refresca SOLO los documentos de origen
        organizacional cuyo slot cambio (agregado / modificado / quitado),
        preservando los documentos nativos de la admision (cargados admision-side)
        y los de origen organizacional NO modificados. No resetea ``tipo_convenio``
        ni ``estado`` (a diferencia de ``resync_admision_desde_organizacion``, que
        aplica cuando cambio el Tipo de Entidad y reconstruye todo)."""
        organizacion = getattr(getattr(admision, "comedor", None), "organizacion", None)
        if not organizacion:
            return False, "La admision no tiene organizacion asociada."

        actuales = AdmisionService._tokens_org_actuales(admision)
        snapshots = {
            snap.slot_key: snap
            for snap in AdmisionDocOrgSnapshot.objects.filter(admision=admision)
        }
        slots_a_refrescar = set()
        for slot, data in actuales.items():
            snap = snapshots.get(slot)
            if snap is None or snap.token != data["token"]:
                slots_a_refrescar.add(slot)  # agregado / modificado
        for slot in snapshots:
            if slot not in actuales:
                slots_a_refrescar.add(slot)  # quitado del legajo

        if not slots_a_refrescar:
            AdmisionService.refrescar_snapshot_documentacion_organizacional(admision)
            return True, "La documentacion ya estaba actualizada con el Legajo."

        # Borrar SOLO los ArchivoAdmision de origen organizacional de los slots
        # que cambiaron. Nunca se tocan los documentos nativos de la admision
        # (sin archivo_organizacion_origen) ni los de origen organizacional no
        # modificados.
        borrados = 0
        for archivo_adm in ArchivoAdmision.objects.filter(
            admision=admision, archivo_organizacion_origen__isnull=False
        ).select_related("archivo_organizacion_origen"):
            origin = archivo_adm.archivo_organizacion_origen
            if origin.documentacion_id:
                slot = f"doc:{origin.documentacion_id}"
            else:
                slot = f"custom:{origin.id}"
            if slot in slots_a_refrescar:
                archivo_adm.delete()
                borrados += 1

        # Re-materializar (aditivo): re-crea desde el legajo los slots borrados que
        # siguen vigentes; los quitados no se re-crean; preserva nativos y los no
        # modificados (congelar saltea los que ya existen).
        AdmisionService.congelar_documentacion_organizacional(admision, user)
        AdmisionService.refrescar_snapshot_documentacion_organizacional(admision)
        logger.info(
            "Documentacion de admision actualizada (dirigida) desde la organizacion",
            extra={
                "admision_pk": admision.pk,
                "slots_refrescados": sorted(slots_a_refrescar),
                "archivos_borrados": borrados,
            },
        )
        return True, "Documentacion actualizada desde el Legajo de la Organizacion."

    # ------------------------------------------------------------------
    # Issue #1799 Req 1: deteccion de cambios en la documentacion del legajo
    # ------------------------------------------------------------------
    @staticmethod
    def _org_archivos_relevantes(admision):
        """Archivos del legajo de la organizacion que alimentan a esta admision:
        los vigentes de la categoria documental (catalogo) mas los adicionales
        (personalizados)."""
        organizacion = getattr(getattr(admision, "comedor", None), "organizacion", None)
        if not organizacion:
            return []
        relevantes = []
        categoria = AdmisionService._categoria_organizacional_admision(admision)
        if categoria:
            vigentes = AdmisionService._get_archivos_organizacion_vigentes(
                admision, categoria
            )
            relevantes.extend(vigentes.values())
        relevantes.extend(
            ArchivoOrganizacion.objects.filter(
                organizacion=organizacion, documentacion__isnull=True
            )
        )
        return relevantes

    @staticmethod
    def _tokens_org_actuales(admision):
        """Mapa ``slot_key -> {etiqueta, token}`` del estado actual del legajo.
        El token excluye el numero_gde (se replica aparte, Req 3) y las
        observaciones internas; captura archivo, estado y vencimiento."""
        actuales = {}
        for archivo in AdmisionService._org_archivos_relevantes(admision):
            if not archivo.archivo:
                continue
            if archivo.es_personalizado:
                slot = f"custom:{archivo.id}"
            else:
                slot = f"doc:{archivo.documentacion_id}"
            token = "|".join(
                [
                    str(archivo.id),
                    str(archivo.estado or ""),
                    str(getattr(archivo.archivo, "name", "") or ""),
                    str(archivo.fecha_vencimiento or ""),
                ]
            )
            actuales[slot] = {"etiqueta": archivo.nombre_documento, "token": token}
        return actuales

    @staticmethod
    def refrescar_snapshot_documentacion_organizacional(admision):
        """Deja el snapshot de la admision igual al estado actual del legajo
        (upsert + limpieza de slots obsoletos). Se invoca al crear la admision,
        al resincronizar y al aceptar la divergencia."""
        if not admision or not admision.pk:
            return
        actuales = AdmisionService._tokens_org_actuales(admision)
        existentes = {
            snap.slot_key: snap
            for snap in AdmisionDocOrgSnapshot.objects.filter(admision=admision)
        }
        for slot, data in actuales.items():
            snap = existentes.pop(slot, None)
            if snap is None:
                AdmisionDocOrgSnapshot.objects.create(
                    admision=admision,
                    slot_key=slot,
                    etiqueta=data["etiqueta"],
                    token=data["token"],
                )
            elif snap.token != data["token"] or snap.etiqueta != data["etiqueta"]:
                snap.token = data["token"]
                snap.etiqueta = data["etiqueta"]
                snap.save(update_fields=["token", "etiqueta", "synced_at"])
        if existentes:
            AdmisionDocOrgSnapshot.objects.filter(
                admision=admision, slot_key__in=list(existentes.keys())
            ).delete()

    @staticmethod
    def admision_documentacion_desactualizada(admision):
        """Devuelve ``(bool, [labels])``: si la documentacion del legajo cambio
        respecto del snapshot de la admision, y la lista de documentos
        modificados/agregados/eliminados. Admisiones sin snapshot (legacy o
        recien creadas) se inicializan en sync (req 1.6)."""
        if not admision or not admision.pk:
            return False, []
        organizacion = getattr(getattr(admision, "comedor", None), "organizacion", None)
        if not organizacion:
            return False, []

        existentes = {
            snap.slot_key: snap
            for snap in AdmisionDocOrgSnapshot.objects.filter(admision=admision)
        }
        actuales = AdmisionService._tokens_org_actuales(admision)
        if not existentes:
            AdmisionService.refrescar_snapshot_documentacion_organizacional(admision)
            return False, []

        modificados = []
        for slot, data in actuales.items():
            snap = existentes.get(slot)
            if snap is None or snap.token != data["token"]:
                modificados.append(data["etiqueta"])
        for slot, snap in existentes.items():
            if slot not in actuales:
                modificados.append(snap.etiqueta or "Documento")

        labels = []
        vistos = set()
        for etiqueta in modificados:
            if etiqueta not in vistos:
                vistos.add(etiqueta)
                labels.append(etiqueta)
        return (len(labels) > 0), labels

    @staticmethod
    def update_convenio(admision, nuevo_convenio_id):

        try:

            if not nuevo_convenio_id:

                return False

            nuevo_convenio = TipoConvenio.objects.get(pk=nuevo_convenio_id)

            AdmisionService._aplicar_cambio_convenio_y_reset_documentos(
                admision, nuevo_convenio
            )

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
    def _normalizar_nombre_tipo(nombre):
        texto = unicodedata.normalize("NFKD", nombre or "")
        texto = "".join(c for c in texto if not unicodedata.combining(c))
        return re.sub(r"\s+", " ", texto).strip().lower()

    @staticmethod
    def resolver_tipo_convenio_desde_organizacion(organizacion):
        tipo_entidad = getattr(organizacion, "tipo_entidad", None)
        tipo_entidad_nombre = AdmisionService._normalizar_nombre_tipo(
            getattr(tipo_entidad, "nombre", "")
        )
        convenio_nombre = AdmisionService.TIPO_ENTIDAD_A_CONVENIO.get(
            tipo_entidad_nombre
        )
        if not convenio_nombre:
            return None

        for convenio in TipoConvenio.objects.exclude(id=4):
            if (
                AdmisionService._normalizar_nombre_tipo(convenio.nombre)
                == convenio_nombre
            ):
                return convenio
        return None

    @staticmethod
    def asegurar_tipo_convenio_desde_organizacion(admision):
        if not admision or admision.tipo_convenio_id:
            return admision

        tipo_convenio = AdmisionService.resolver_tipo_convenio_desde_organizacion(
            getattr(getattr(admision, "comedor", None), "organizacion", None)
        )
        if not tipo_convenio:
            return admision

        admision.tipo_convenio = tipo_convenio
        admision.estado_admision = admision.estado_admision or "convenio_seleccionado"
        admision.save(update_fields=["tipo_convenio", "estado_admision"])
        return admision

    @staticmethod
    def confirmar_tipo_convenio_desde_organizacion(admision):
        tipo_convenio = AdmisionService.resolver_tipo_convenio_desde_organizacion(
            getattr(getattr(admision, "comedor", None), "organizacion", None)
        )
        if not tipo_convenio:
            return (
                False,
                "No se pudo resolver el Tipo de Convenio desde el Tipo de Entidad de la organización.",
            )

        admision.tipo_convenio = tipo_convenio
        admision.estado_admision = "convenio_seleccionado"
        admision.save(update_fields=["tipo_convenio", "estado_admision"])
        AdmisionService.congelar_documentacion_organizacional(admision)
        return True, "Tipo de convenio precargado desde la organización."

    @staticmethod
    def _procesar_post_confirmar_tipo_convenio(admision):
        return AdmisionService.confirmar_tipo_convenio_desde_organizacion(admision)

    @staticmethod
    def _build_defaults_handle_file_upload(archivo, usuario=None):
        defaults = {
            "archivo": archivo,
            "estado": "Documento adjunto",
            "numero_gde": None,
            "nombre_personalizado": None,
        }
        if usuario and usuario.is_authenticated:
            defaults["modificado_por"] = usuario
        return defaults

    @staticmethod
    def _postprocesar_archivo_admision_creado(
        archivo_admision, created, admision, usuario=None
    ):
        if created and usuario and usuario.is_authenticated:
            archivo_admision.creado_por = usuario
            archivo_admision.save(update_fields=["creado_por"])

        if created and admision.estado_admision == "convenio_seleccionado":
            AdmisionService.actualizar_estado_admision(admision, "cargar_documento")
            admision.save()

    @staticmethod
    def handle_file_upload(admision_id, documentacion_id, archivo, usuario=None):

        try:

            admision = get_object_or_404(Admision, pk=admision_id)
            error_modificacion = (
                AdmisionService._validar_modificacion_documental_por_tecnico(
                    usuario, admision
                )
            )
            if error_modificacion:
                return None, False

            documentacion = get_object_or_404(Documentacion, pk=documentacion_id)

            defaults = AdmisionService._build_defaults_handle_file_upload(
                archivo, usuario
            )

            archivo_admision, created = ArchivoAdmision.objects.update_or_create(
                admision=admision,
                documentacion=documentacion,
                defaults=defaults,
            )
            AdmisionService._postprocesar_archivo_admision_creado(
                archivo_admision=archivo_admision,
                created=created,
                admision=admision,
                usuario=usuario,
            )
            AdmisionService._limpiar_if_gde_admision_por_cambio_documental(admision)

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
    def _normalizar_y_validar_documento_personalizado(nombre, archivo):
        nombre = (nombre or "").strip()
        if not nombre:
            return None, None, "Debe indicar un nombre para el documento."
        if not archivo:
            return None, None, "Debe adjuntar un archivo."
        return nombre[:255], archivo, None

    @staticmethod
    def _verificar_permiso_documento_personalizado(usuario, admision):
        if usuario.is_superuser:
            return True, None

        comedor = admision.comedor
        if not comedor or not AdmisionService._verificar_permiso_dupla(
            usuario, comedor
        ):
            return False, "Sin permisos para modificar esta admision."
        return True, None

    @staticmethod
    def crear_documento_personalizado(admision_id, nombre, archivo, usuario):

        try:

            nombre, archivo, validation_error = (
                AdmisionService._normalizar_y_validar_documento_personalizado(
                    nombre, archivo
                )
            )
            if validation_error:
                return None, validation_error

            admision = get_object_or_404(Admision, pk=admision_id)
            has_permission, permission_error = (
                AdmisionService._verificar_permiso_documento_personalizado(
                    usuario, admision
                )
            )
            if not has_permission:
                return None, permission_error
            error_modificacion = (
                AdmisionService._validar_modificacion_documental_por_tecnico(
                    usuario, admision
                )
            )
            if error_modificacion:
                return None, error_modificacion

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
                AdmisionService._limpiar_if_gde_admision_por_cambio_documental(admision)

            return archivo_admision, None

        except Exception:

            logger.exception(
                "Error en crear_documento_personalizado",
                extra={"admision_id": admision_id, "nombre": nombre},
            )

            return None, "No se pudo guardar el documento."

    @staticmethod
    def delete_admision_file(archivo, user=None, hard=False):

        try:

            documentacion = archivo.documentacion

            if hard and archivo.archivo:

                file_path = os.path.join(settings.MEDIA_ROOT, str(archivo.archivo))

                if os.path.exists(file_path):

                    os.remove(file_path)

            if hasattr(archivo, "hard_delete") and not hard:
                archivo.delete(user=user, cascade=True)
            elif hasattr(archivo, "hard_delete") and hard:
                archivo.hard_delete()
            else:
                archivo.delete()

            AdmisionService._limpiar_if_gde_admision_por_cambio_documental(
                archivo.admision
            )

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
    def _parse_payload_actualizar_estado_ajax(request):
        estado = request.POST.get("estado")
        documento_id = request.POST.get("documento_id")
        admision_id = request.POST.get("admision_id")
        if not all([estado, documento_id, admision_id]):
            return None, None, None, {"success": False, "error": "Datos incompletos."}
        return estado, documento_id, admision_id, None

    @staticmethod
    def _validar_permiso_actualizar_estado_ajax(request, admision):
        if request.user.is_superuser:
            return None

        comedor = admision.comedor
        if not comedor:
            return {"success": False, "error": "Admision sin comedor asociado."}

        if not AdmisionService._verificar_permiso_dupla(request.user, comedor):
            return {
                "success": False,
                "error": "Sin permisos para modificar esta admision.",
            }

        return None

    @staticmethod
    def _build_success_actualizar_estado_ajax_response(
        archivo, display_objetivo, grupo_usuario, request=None
    ):
        return {
            "success": True,
            "nuevo_estado": display_objetivo,
            "grupo_usuario": grupo_usuario,
            "observaciones": archivo.observaciones,
            # Re-render de la celda "Número de GDE": al cambiar el estado del
            # documento (p.ej. -> Aceptado) debe aparecer/ocultarse el campo GDE
            # sin recargar la pagina (issue #1799, feedback punto 4).
            "gde_html": AdmisionService._render_celda_gde_html(archivo, request),
        }

    @staticmethod
    def _render_celda_gde_html(archivo, request):
        """Renderiza el interior de la celda GDE de un ArchivoAdmision para
        inyectarlo via AJAX. Devuelve None si no hay request o si el render falla:
        el re-render es auxiliar y NUNCA debe romper la actualizacion de estado."""
        if request is None or archivo is None:
            return None
        try:
            if archivo.documentacion_id:
                doc = AdmisionService._serialize_documentacion(
                    archivo.documentacion, archivo
                )
            else:
                doc = AdmisionService.serialize_documento_personalizado(archivo)
            return render_to_string(
                "admisiones/includes/gde_cell.html",
                {"doc": doc, "admision": archivo.admision},
                request=request,
            )
        except Exception:
            logger.exception(
                "No se pudo renderizar la celda GDE para el re-render AJAX",
                extra={"archivo_pk": getattr(archivo, "pk", None)},
            )
            return None

    @staticmethod
    def _resolver_estado_y_observacion_actualizar_estado_ajax(request):
        estado = request.POST.get("estado")
        grupo_usuario = AdmisionService.get_dupla_grupo_por_usuario(request.user)
        observacion = (request.POST.get("observacion", "") or "").strip()
        display_objetivo, estado_canonico = AdmisionService._normalize_estado_display(
            estado
        )
        return grupo_usuario, observacion, display_objetivo, estado_canonico

    @staticmethod
    def _validar_observacion_rectificar_actualizar_estado_ajax(
        display_objetivo, grupo_usuario, observacion
    ):
        requiere_observacion = (
            display_objetivo.lower() == "rectificar"
            and grupo_usuario == "Abogado Dupla"
        )
        if requiere_observacion and not observacion:
            return {
                "success": False,
                "error": "Debe ingresar observaciones para rectificar.",
            }
        return None

    @staticmethod
    def _aplicar_observacion_archivo(archivo, observacion):
        if observacion is None:
            return
        archivo.observaciones = (
            observacion.strip() if isinstance(observacion, str) else observacion
        )

    @staticmethod
    def _persistir_cambio_estado_archivo(archivo, estado_normalizado):
        archivo.estado = estado_normalizado
        archivo.save()
        AdmisionService._actualizar_estados_por_cambio_documento(
            archivo.admision, estado_normalizado
        )

    @staticmethod
    def actualizar_estado_ajax(request):

        try:
            estado, documento_id, admision_id, payload_error = (
                AdmisionService._parse_payload_actualizar_estado_ajax(request)
            )
            if payload_error:
                return payload_error

            admision = get_object_or_404(Admision, pk=admision_id)
            permission_error = AdmisionService._validar_permiso_actualizar_estado_ajax(
                request, admision
            )
            if permission_error:
                return permission_error
            error_modificacion = (
                AdmisionService._validar_modificacion_documental_por_tecnico(
                    request.user, admision
                )
            )
            if error_modificacion:
                return {"success": False, "error": error_modificacion}

            archivo = get_object_or_404(
                ArchivoAdmision.objects.select_related("admision", "documentacion"),
                id=documento_id,
                admision_id=admision_id,
            )

            grupo_usuario, observacion, display_objetivo, estado_canonico = (
                AdmisionService._resolver_estado_y_observacion_actualizar_estado_ajax(
                    request
                )
            )
            observacion_error = (
                AdmisionService._validar_observacion_rectificar_actualizar_estado_ajax(
                    display_objetivo, grupo_usuario, observacion
                )
            )
            if observacion_error:
                return observacion_error

            exito = AdmisionService.update_estado_archivo(
                archivo,
                estado_canonico,
                observacion if observacion else None,
            )

            if not exito:

                return {"success": False, "error": "No se pudo actualizar el estado."}

            return AdmisionService._build_success_actualizar_estado_ajax_response(
                archivo=archivo,
                display_objetivo=display_objetivo,
                grupo_usuario=grupo_usuario,
                request=request,
            )

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
            AdmisionService._aplicar_observacion_archivo(archivo, observacion)
            AdmisionService._persistir_cambio_estado_archivo(
                archivo, estado_normalizado
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

            if not AdmisionService._puede_verificar_documentacion_admision(admision):
                return

            if not AdmisionService._todos_obligatorios_aceptados(admision):
                return

            AdmisionService._aprobar_documentacion_obligatoria_admision(admision)

        except Exception:

            logger.exception(
                "Error en verificar_estado_admision",
                extra={"admision_pk": getattr(admision, "pk", None)},
            )

    @staticmethod
    def _puede_verificar_documentacion_admision(admision):

        return getattr(admision, "estado_id", None) != 3

    @staticmethod
    def _aprobar_documentacion_obligatoria_admision(admision):

        if admision.estado_id == 2:

            return False

        admision.estado_id = 2
        admision.save()

        AdmisionService.actualizar_estado_admision(admision, "aprobar_documentacion")

        return True

    @staticmethod
    def get_dupla_grupo_por_usuario(user):

        try:

            if user_has_any_permission_codes(
                user,
                [
                    "comedores.view_comedor",
                    "admisiones.view_admision",
                    "acompanamientos.view_informacionrelevante",
                ],
            ):

                return "Abogado Dupla"

            elif user_has_any_permission_codes(
                user,
                [
                    "comedores.view_comedor",
                    "admisiones.view_admision",
                    "acompanamientos.view_informacionrelevante",
                ],
            ):

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
    def _set_attr_if_changed(instance, field_name, new_value):

        if getattr(instance, field_name) == new_value:

            return False

        setattr(instance, field_name, new_value)

        return True

    @staticmethod
    def _clear_attr_if_present(instance, field_name):

        if not getattr(instance, field_name):

            return False

        setattr(instance, field_name, None)

        return True

    @staticmethod
    def _save_admision_if_changed(admision, cambios):

        if not cambios:

            return False

        admision.save()

        return True

    @staticmethod
    def marcar_como_enviado_a_legales(admision, usuario=None):

        try:

            if not admision.enviado_legales:

                AdmisionService._set_attr_if_changed(admision, "enviado_legales", True)
                AdmisionService._set_attr_if_changed(
                    admision, "estado_legales", "Enviado a Legales"
                )
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

            form = IFInformeTecnicoForm(request.POST, request.FILES, instance=admision)

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

                AdmisionService._set_attr_if_changed(
                    admision, "enviado_acompaniamiento", True
                )
                AdmisionService._set_attr_if_changed(
                    admision, "estado_legales", "Acompañamiento Iniciado"
                )
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

            cambios = (
                AdmisionService._set_attr_if_changed(admision, "enviado_legales", True)
                or cambios
            )
            cambios = (
                AdmisionService._set_attr_if_changed(admision, "estado_id", 2)
                or cambios
            )
            cambios = (
                AdmisionService._set_attr_if_changed(
                    admision, "estado_legales", "Rectificado"
                )
                or cambios
            )
            cambios = (
                AdmisionService._clear_attr_if_present(admision, "observaciones")
                or cambios
            )

            return AdmisionService._save_admision_if_changed(admision, cambios)

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

            AcompanamientoService.importar_datos_desde_admision(admision)

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

            comedor = get_object_or_404(
                Comedor.objects.select_related("organizacion__tipo_entidad"),
                id=comedor_id,
            )
            tipo_convenio = AdmisionService.resolver_tipo_convenio_desde_organizacion(
                comedor.organizacion
            )

            return {
                "comedor": comedor,
                "tipo_convenio_precargado": tipo_convenio,
            }
        except Exception:
            logger.exception(
                "Error en get_admision_create_context",
                extra={"comedor_id": comedor_id},
            )
            return {}

    @staticmethod
    def create_admision(comedor_id, tipo_convenio_id=None):
        del tipo_convenio_id
        try:
            from comedores.models import Comedor

            comedor = get_object_or_404(
                Comedor.objects.select_related(
                    "programa", "organizacion__tipo_entidad"
                ),
                id=comedor_id,
            )
            if not comedor_usa_admision_para_nomina(comedor):
                logger.warning(
                    "Se intentó crear una admisión en un comedor con nómina directa",
                    extra={"comedor_id": comedor_id},
                )
                return None
            tipo_convenio = AdmisionService.resolver_tipo_convenio_desde_organizacion(
                comedor.organizacion
            )
            if not tipo_convenio:
                logger.warning(
                    "No se pudo resolver tipo de convenio desde tipo de entidad",
                    extra={"comedor_id": comedor_id},
                )
                return None
            estado_inicial = EstadoAdmision.objects.first()

            admision = Admision.objects.create(
                comedor=comedor,
                tipo_convenio=tipo_convenio,
                estado=estado_inicial,
                tipo="incorporacion",
                estado_admision="convenio_seleccionado",
                tipo_entidad_origen=getattr(comedor.organizacion, "tipo_entidad", None),
            )
            AdmisionService.congelar_documentacion_organizacional(admision)
            AdmisionService.refrescar_snapshot_documentacion_organizacional(admision)

            return admision
        except Exception:
            logger.exception(
                "Error en create_admision",
                extra={"comedor_id": comedor_id},
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
    def _build_error_response_actualizar_numero_gde(message):
        return {"success": False, "error": message}

    @staticmethod
    def _parse_actualizar_numero_gde_payload(request):
        documento_id = request.POST.get("documento_id")
        numero_gde = request.POST.get("numero_gde", "").strip()
        return documento_id, numero_gde

    @staticmethod
    def _puede_editar_numero_gde(user, archivo):
        return user.is_superuser or AdmisionService._verificar_permiso_dupla(
            user, archivo.admision.comedor
        )

    @staticmethod
    def _obtener_ultimo_informe_tecnico(admision):
        return (
            InformeTecnico.objects.filter(admision=admision, tipo="base")
            .order_by("-id")
            .only("estado", "estado_formulario")
            .first()
        )

    @staticmethod
    def _validar_modificacion_documental_por_tecnico(user, admision):
        comedor = getattr(admision, "comedor", None)
        if (
            not user
            or getattr(user, "is_superuser", False)
            or not admision
            or not comedor
        ):
            return None
        if not AdmisionService._verificar_permiso_tecnico_dupla(user, comedor):
            return None

        informe = AdmisionService._obtener_ultimo_informe_tecnico(admision)
        if not informe:
            return None

        if informe.estado != "Iniciado" and informe.estado_formulario != "borrador":
            return (
                "No puede modificar documentos cuando el informe tecnico ya no esta "
                "iniciado ni en borrador."
            )
        return None

    @staticmethod
    def _limpiar_if_gde_admision_por_cambio_documental(admision):
        if not admision:
            return

        update_fields = []
        if getattr(admision, "numero_if_tecnico", None):
            admision.numero_if_tecnico = None
            update_fields.append("numero_if_tecnico")
        if getattr(admision, "archivo_informe_tecnico_GDE", None):
            admision.archivo_informe_tecnico_GDE = None
            update_fields.append("archivo_informe_tecnico_GDE")
        if getattr(admision, "estado_admision", None) == "if_informe_tecnico_cargado":
            admision.estado_admision = "informe_tecnico_aprobado"
            update_fields.append("estado_admision")
        else:
            nuevo_estado_documental = (
                AdmisionService._resolver_estado_documental_por_cambio_documental(
                    admision
                )
            )
            if (
                nuevo_estado_documental
                and nuevo_estado_documental != admision.estado_admision
            ):
                admision.estado_admision = nuevo_estado_documental
                update_fields.append("estado_admision")

        if update_fields:
            admision.save(update_fields=update_fields)

    @staticmethod
    def replicar_numero_gde_desde_organizacion(archivo_org, user=None):
        """Issue #1799 Req 3: el Numero de GDE se carga en el legajo de la
        Organizacion (unica fuente) y se replica a los ``ArchivoAdmision``
        materializados desde ese archivo, en todas las admisiones activas
        relacionadas. Devuelve la cantidad de admisiones actualizadas."""
        if not archivo_org:
            return 0
        materializados = ArchivoAdmision.objects.filter(
            archivo_organizacion_origen_id=archivo_org.id,
            admision__enviada_a_archivo=False,
        ).select_related("admision")
        actualizados = 0
        for archivo_adm in materializados:
            if archivo_adm.numero_gde == archivo_org.numero_gde:
                continue
            archivo_adm.numero_gde = archivo_org.numero_gde
            if user is not None and getattr(user, "is_authenticated", False):
                archivo_adm.modificado_por = user
            archivo_adm.save(
                update_fields=["numero_gde", "modificado_por", "modificado"]
            )
            AdmisionService._limpiar_if_gde_admision_por_cambio_documental(
                archivo_adm.admision
            )
            actualizados += 1
        return actualizados

    @staticmethod
    def _resolver_estado_documental_por_cambio_documental(admision):
        estado_admision = getattr(admision, "estado_admision", None)
        if estado_admision not in {
            "documentacion_finalizada",
            "documentacion_aprobada",
            "documentacion_carga_finalizada",
        }:
            return None

        if not AdmisionService._todos_obligatorios_tienen_archivos(admision):
            return "documentacion_en_proceso"

        if estado_admision in {
            "documentacion_aprobada",
            "documentacion_carga_finalizada",
        } and not AdmisionService._todos_obligatorios_aceptados(admision):
            return "documentacion_finalizada"

        if estado_admision == "documentacion_carga_finalizada":
            return "documentacion_aprobada"

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

            documento_id, numero_gde = (
                AdmisionService._parse_actualizar_numero_gde_payload(request)
            )

            if not documento_id:
                return AdmisionService._build_error_response_actualizar_numero_gde(
                    "ID de documento requerido."
                )

            archivo = get_object_or_404(ArchivoAdmision, id=documento_id)

            if archivo.estado != "Aceptado":
                return AdmisionService._build_error_response_actualizar_numero_gde(
                    "Solo se puede actualizar el número GDE en documentos aceptados."
                )

            if archivo.archivo_organizacion_origen_id:
                # Issue #1799 Req 3: el GDE de documentos de origen organizacional
                # se gestiona desde el Legajo de la Organizacion (unica fuente).
                return AdmisionService._build_error_response_actualizar_numero_gde(
                    "El número de GDE de documentos de la Organización se gestiona "
                    "desde el Legajo de la Organización."
                )

            if not AdmisionService._puede_editar_numero_gde(request.user, archivo):
                return AdmisionService._build_error_response_actualizar_numero_gde(
                    "No tiene permisos para editar este documento."
                )
            error_modificacion = (
                AdmisionService._validar_modificacion_documental_por_tecnico(
                    request.user, archivo.admision
                )
            )
            if error_modificacion:
                return AdmisionService._build_error_response_actualizar_numero_gde(
                    error_modificacion
                )

            valor_anterior = archivo.numero_gde

            archivo.numero_gde = numero_gde if numero_gde else None

            archivo.save()
            AdmisionService._limpiar_if_gde_admision_por_cambio_documental(
                archivo.admision
            )

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
    def actualizar_numero_gde_organizacion_ajax(request):
        """Actualiza el numero GDE asociado a un ``ArchivoOrganizacion`` para
        una admision puntual usando el modelo ``NumeroGdeOrganizacion``.
        Reglas:
        - solo se permite cuando ``ArchivoOrganizacion.estado == 'Aceptado'``,
        - solo el tecnico de la dupla (o superuser) puede editar,
        - se aplican las mismas restricciones documentales que para los
          ``ArchivoAdmision`` (informe tecnico ya no en borrador).
        """

        archivo_org_id = (request.POST.get("archivo_organizacion_id") or "").strip()
        admision_id = (request.POST.get("admision_id") or "").strip()
        numero_gde = (request.POST.get("numero_gde") or "").strip() or None
        try:
            if not archivo_org_id or not admision_id:
                return AdmisionService._build_error_response_actualizar_numero_gde(
                    "Faltan parametros admision o archivo de organizacion."
                )

            admision = get_object_or_404(
                Admision.objects.select_related("comedor__organizacion"),
                pk=admision_id,
            )
            archivo_org = get_object_or_404(
                ArchivoOrganizacion.objects.select_related("organizacion"),
                pk=archivo_org_id,
            )

            organizacion_admision = getattr(
                getattr(admision, "comedor", None), "organizacion", None
            )
            if (
                not organizacion_admision
                or organizacion_admision.pk != archivo_org.organizacion_id
            ):
                return AdmisionService._build_error_response_actualizar_numero_gde(
                    "El archivo no pertenece a la organizacion de la admision."
                )

            if archivo_org.estado != ArchivoOrganizacion.ESTADO_ACEPTADO:
                return AdmisionService._build_error_response_actualizar_numero_gde(
                    "Solo se puede actualizar el numero GDE en documentos aceptados."
                )

            if not (
                request.user.is_superuser
                or AdmisionService._verificar_permiso_dupla(
                    request.user, admision.comedor
                )
            ):
                return AdmisionService._build_error_response_actualizar_numero_gde(
                    "No tiene permisos para editar este documento."
                )

            error_modificacion = (
                AdmisionService._validar_modificacion_documental_por_tecnico(
                    request.user, admision
                )
            )
            if error_modificacion:
                return AdmisionService._build_error_response_actualizar_numero_gde(
                    error_modificacion
                )

            registro, _ = NumeroGdeOrganizacion.objects.get_or_create(
                admision=admision,
                archivo_organizacion=archivo_org,
                defaults={"modificado_por": request.user},
            )
            valor_anterior = registro.numero_gde
            registro.numero_gde = numero_gde
            registro.modificado_por = request.user
            registro.save(update_fields=["numero_gde", "modificado_por", "modificado"])

            AdmisionService._limpiar_if_gde_admision_por_cambio_documental(admision)

            logger.info(
                "Numero GDE de organizacion actualizado",
                extra={
                    "admision_id": admision.id,
                    "archivo_organizacion_id": archivo_org.id,
                    "valor_anterior": valor_anterior,
                    "valor_nuevo": numero_gde,
                },
            )
            return {
                "success": True,
                "numero_gde": registro.numero_gde,
                "valor_anterior": valor_anterior,
            }
        except Exception as exc:
            logger.exception(
                "Error en actualizar_numero_gde_organizacion_ajax",
                extra={
                    "archivo_organizacion_id": archivo_org_id,
                    "admision_id": admision_id,
                    "numero_gde": numero_gde,
                },
            )
            return {"success": False, "error": str(exc)}

    @staticmethod
    def _build_error_response_actualizar_convenio_numero(message):
        return {"success": False, "error": message}

    @staticmethod
    def _parse_actualizar_convenio_payload(request):
        admision_id = request.POST.get("admision_id")
        convenio_numero_raw = request.POST.get("convenio_numero", "").strip()
        return admision_id, convenio_numero_raw

    @staticmethod
    def _parse_convenio_numero_value(convenio_numero_raw):
        if convenio_numero_raw == "":
            return None, None

        try:
            nuevo_valor = int(convenio_numero_raw)
        except ValueError:
            return None, "Debe ingresar un numero valido."

        if nuevo_valor < 0:
            return None, "El numero de convenio no puede ser negativo."

        return nuevo_valor, None

    @staticmethod
    def _puede_editar_convenio_numero(user, admision):
        return user.is_superuser or AdmisionService._verificar_permiso_tecnico_dupla(
            user, admision.comedor
        )

    @staticmethod
    def actualizar_convenio_numero_ajax(request):
        """
        Actualiza el numero de convenio de una admision via AJAX.
        """
        try:
            admision_id, convenio_numero_raw = (
                AdmisionService._parse_actualizar_convenio_payload(request)
            )

            if not admision_id:
                return AdmisionService._build_error_response_actualizar_convenio_numero(
                    "ID de admision requerido."
                )

            admision = get_object_or_404(Admision, id=admision_id)

            if not AdmisionService._puede_editar_convenio_numero(
                request.user, admision
            ):
                return AdmisionService._build_error_response_actualizar_convenio_numero(
                    "No tiene permisos para editar esta admision."
                )

            nuevo_valor, parse_error = AdmisionService._parse_convenio_numero_value(
                convenio_numero_raw
            )
            if parse_error:
                return AdmisionService._build_error_response_actualizar_convenio_numero(
                    parse_error
                )

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
    def _build_error_response_actualizar_num_expediente(message):
        return {"success": False, "error": message}

    @staticmethod
    def _parse_actualizar_num_expediente_payload(request):
        admision_id = request.POST.get("admision_id")
        numero_raw = request.POST.get("num_expediente", "").strip()
        return admision_id, numero_raw

    @staticmethod
    def _puede_editar_num_expediente(user, admision):
        if admision.enviado_legales:
            return False
        return user.is_superuser or AdmisionService._verificar_permiso_tecnico_dupla(
            user, admision.comedor
        )

    @staticmethod
    def actualizar_num_expediente_ajax(request):
        try:
            admision_id, numero_raw = (
                AdmisionService._parse_actualizar_num_expediente_payload(request)
            )

            if not admision_id:
                return AdmisionService._build_error_response_actualizar_num_expediente(
                    "ID de admisión requerido."
                )

            if not numero_raw:
                return AdmisionService._build_error_response_actualizar_num_expediente(
                    "El número de expediente es obligatorio."
                )

            admision = get_object_or_404(Admision, id=admision_id)

            if not AdmisionService._puede_editar_num_expediente(request.user, admision):
                if admision.enviado_legales:
                    return AdmisionService._build_error_response_actualizar_num_expediente(
                        "No se puede editar el expediente una vez enviado a legales."
                    )
                return AdmisionService._build_error_response_actualizar_num_expediente(
                    "No tiene permisos para editar esta admisión."
                )

            valor_anterior = admision.num_expediente
            admision.num_expediente = numero_raw or None
            admision.save(update_fields=["num_expediente"])

            logger.info(
                "Numero de expediente actualizado: admision_id=%s, valor_anterior=%s, valor_nuevo=%s",
                admision_id,
                valor_anterior,
                admision.num_expediente,
            )

            return {
                "success": True,
                "num_expediente": admision.num_expediente,
                "valor_anterior": valor_anterior,
            }

        except Exception as exc:
            logger.exception(
                "Error en actualizar_num_expediente_ajax",
                extra={"admision_id": locals().get("admision_id")},
            )
            return {"success": False, "error": str(exc)}

    @staticmethod
    def _verificar_permiso_tecnico_dupla(user, comedor):
        """Verifica que el usuario sea técnico de la dupla asignada al comedor"""

        try:

            return (
                user_has_any_permission_codes(
                    user,
                    [
                        "comedores.view_comedor",
                        "admisiones.view_admision",
                        "acompanamientos.view_informacionrelevante",
                    ],
                )
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
        es_tecnico, es_abogado = AdmisionService._resolver_roles_para_botones(user)

        AdmisionService._append_botones_generales_admision(
            botones,
            admision,
            es_tecnico,
        )
        AdmisionService._append_botones_tecnico_admision(
            botones,
            admision,
            informe_tecnico,
            mostrar_informe_complementario,
            es_tecnico,
        )
        AdmisionService._append_botones_abogado_admision(
            botones,
            admision,
            informe_tecnico,
            es_abogado,
        )

        return botones

    @staticmethod
    def _resolver_roles_para_botones(user):
        if not user:
            return False, False
        es_tecnico = user_has_permission_code(user, "auth.role_tecnico_comedor")
        es_abogado = user_has_permission_code(user, "auth.role_abogado_dupla")
        return es_tecnico, es_abogado

    @staticmethod
    def _get_boton_tecnico_informe(admision, informe_tecnico):
        if admision.estado_admision == "expediente_cargado" and not informe_tecnico:
            return "crear_informe_tecnico"
        if (
            admision.estado_admision == "informe_tecnico_en_proceso"
            and informe_tecnico
            and informe_tecnico.estado in ["Iniciado", "Para revision"]
            and informe_tecnico.estado_formulario == "borrador"
        ):
            return "editar_informe_tecnico"
        if informe_tecnico and informe_tecnico.estado == "A subsanar":
            return "editar_informe_tecnico"
        if (
            admision.estado_admision == "informe_tecnico_finalizado"
            and informe_tecnico
            and informe_tecnico.estado == "Docx generado"
        ):
            return "revisar_informe_tecnico"
        return None

    @staticmethod
    def _puede_ver_informe_tecnico_como_abogado(es_abogado, admision, informe_tecnico):
        return bool(
            es_abogado
            and informe_tecnico
            and admision.estado_admision == "informe_tecnico_docx_editado"
            and informe_tecnico.estado == "Docx editado"
        )

    @staticmethod
    def _append_botones_generales_admision(botones, admision, es_tecnico):
        if (
            es_tecnico
            and admision.numero_disposicion
            and not admision.enviado_acompaniamiento
        ):
            botones.append("comenzar_acompaniamiento")

        if admision.estado_legales == "A Rectificar":
            botones.append("rectificar_documentacion")

    @staticmethod
    def _append_botones_tecnico_admision(
        botones,
        admision,
        informe_tecnico,
        mostrar_informe_complementario,
        es_tecnico,
    ):
        if not es_tecnico:
            return

        if (
            admision.estado_admision == "documentacion_aprobada"
            and not admision.num_expediente
        ):
            botones.append("finalizar_carga_documentacion")

        if (
            admision.estado_admision == "documentacion_carga_finalizada"
            and not admision.num_expediente
        ):
            botones.append("caratular_expediente")

        if admision.num_expediente:
            boton_informe = AdmisionService._get_boton_tecnico_informe(
                admision, informe_tecnico
            )
            if boton_informe:
                botones.append(boton_informe)

        if (
            admision.estado_admision == "informe_tecnico_aprobado"
            and not admision.numero_if_tecnico
        ):
            botones.append("if_informe_tecnico")

        if (
            admision.estado_admision == "if_informe_tecnico_cargado"
            and not admision.enviado_legales
        ):
            botones.append("mandar_a_legales")

        if (
            informe_tecnico
            and informe_tecnico.estado == "Validado"
            and mostrar_informe_complementario
        ):
            botones.append("informe_tecnico_complementario")

    @staticmethod
    def _append_botones_abogado_admision(
        botones, admision, informe_tecnico, es_abogado
    ):
        if AdmisionService._puede_ver_informe_tecnico_como_abogado(
            es_abogado,
            admision,
            informe_tecnico,
        ):
            botones.append("ver_informe_tecnico")

    @staticmethod
    def actualizar_estado_admision(admision, accion):
        """Actualiza el estado_admision basado en la acción realizada"""
        try:
            estado_actual = admision.estado_admision
            nuevo_estado = AdmisionService._transiciones_estado_admision().get(accion)

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
    def _transiciones_estado_admision():

        return {
            "seleccionar_convenio": "convenio_seleccionado",
            "cargar_documento": "documentacion_en_proceso",
            "finalizar_documentacion": "documentacion_finalizada",
            "aprobar_documentacion": "documentacion_aprobada",
            "finalizar_carga_documentacion": "documentacion_carga_finalizada",
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

    @staticmethod
    def _todos_obligatorios_aceptados(admision):
        """Verifica que todos los documentos obligatorios del tipo de convenio estén aceptados"""
        try:
            for (
                doc_obligatorio
            ) in AdmisionService._iter_documentos_obligatorios_admision(admision):
                if not AdmisionService._documento_obligatorio_cumple_requisito(
                    admision=admision,
                    doc_obligatorio=doc_obligatorio,
                    estado="Aceptado",
                    requiere_archivo=False,
                ):
                    return False

            return True

        except Exception:
            logger.exception(
                "Error en _todos_obligatorios_aceptados",
                extra={"admision_pk": admision.pk},
            )
            return False

    @staticmethod
    def _iter_documentos_obligatorios_admision(admision):
        archivos_qs = (
            ArchivoAdmision.objects.filter(admision_id=admision.pk)
            .select_related("admision", "documentacion")
            .order_by("id")
        )
        return Documentacion.objects.filter(
            convenios=admision.tipo_convenio, obligatorio=True
        ).prefetch_related(
            Prefetch(
                "archivoadmision_set",
                queryset=archivos_qs,
                to_attr="archivos_prefetch_para_admision",
            )
        )

    @staticmethod
    def _obtener_archivo_organizacion_para_documentacion_admision(
        admision, documentacion
    ):
        categoria = AdmisionService._categoria_organizacional_admision(admision)
        org_key = AdmisionService._org_doc_key_desde_documentacion_admision(
            documentacion, categoria
        )
        organizacion = getattr(getattr(admision, "comedor", None), "organizacion", None)
        if not org_key or not organizacion:
            return None

        org_doc = (
            DocumentacionOrganizacion.objects.filter(categoria=categoria)
            .filter(nombre__isnull=False)
            .order_by("orden", "id")
        )
        org_doc = next(
            (
                doc
                for doc in org_doc
                if AdmisionService._normalizar_nombre_documental(doc.nombre) == org_key
            ),
            None,
        )
        if not org_doc:
            return None

        return (
            ArchivoOrganizacion.objects.filter(
                organizacion=organizacion,
                documentacion=org_doc,
            )
            .order_by("-creado", "-id")
            .first()
        )

    @staticmethod
    def _existe_archivo_organizacion_obligatorio_admision(
        *,
        admision,
        doc_obligatorio,
        estado=None,
        requiere_archivo=False,
    ):
        archivo = (
            AdmisionService._obtener_archivo_organizacion_para_documentacion_admision(
                admision, doc_obligatorio
            )
        )
        if not archivo:
            return False
        if estado is not None and archivo.estado != estado:
            return False
        if requiere_archivo and not archivo.archivo:
            return False
        return True

    @staticmethod
    def _archivo_cumple_requisito_documental(
        archivo, *, estado=None, requiere_archivo=False
    ):
        if not archivo:
            return False
        if estado is not None and archivo.estado != estado:
            return False
        if requiere_archivo and not archivo.archivo:
            return False
        return True

    @staticmethod
    def _documento_obligatorio_cumple_requisito(
        *,
        admision,
        doc_obligatorio,
        estado=None,
        requiere_archivo=False,
    ):
        archivo_admision = AdmisionService._obtener_archivo_obligatorio_admision(
            admision=admision,
            doc_obligatorio=doc_obligatorio,
            estado=estado,
        )
        if archivo_admision:
            return AdmisionService._archivo_cumple_requisito_documental(
                archivo_admision,
                estado=estado,
                requiere_archivo=requiere_archivo,
            )

        archivo_admision_existente = (
            AdmisionService._obtener_archivo_obligatorio_admision(
                admision=admision,
                doc_obligatorio=doc_obligatorio,
            )
        )
        if archivo_admision_existente:
            return False

        return AdmisionService._existe_archivo_organizacion_obligatorio_admision(
            admision=admision,
            doc_obligatorio=doc_obligatorio,
            estado=estado,
            requiere_archivo=requiere_archivo,
        )

    @staticmethod
    def congelar_documentacion_organizacional(admision, user=None):
        categoria = AdmisionService._categoria_organizacional_admision(admision)
        organizacion = getattr(getattr(admision, "comedor", None), "organizacion", None)
        if not categoria or not organizacion:
            return

        documentaciones = Documentacion.objects.filter(
            convenios=admision.tipo_convenio
        ).order_by("orden", "id")
        docs_admision_por_org_key = {}
        for documentacion in documentaciones:
            org_key = AdmisionService._org_doc_key_desde_documentacion_admision(
                documentacion, categoria
            )
            if org_key:
                docs_admision_por_org_key[org_key] = documentacion

        archivos_org = AdmisionService._get_archivos_organizacion_vigentes(
            admision, categoria
        )
        creo_archivos = False
        for org_doc in DocumentacionOrganizacion.objects.filter(
            categoria=categoria
        ).order_by("orden", "id"):
            archivo_org = archivos_org.get(org_doc.id)
            if not archivo_org or not archivo_org.archivo:
                continue

            org_key = AdmisionService._normalizar_nombre_documental(org_doc.nombre)
            documentacion_admision = docs_admision_por_org_key.get(org_key)
            if (
                documentacion_admision
                and ArchivoAdmision.objects.filter(
                    admision=admision,
                    documentacion=documentacion_admision,
                ).exists()
            ):
                continue
            if (
                not documentacion_admision
                and ArchivoAdmision.objects.filter(
                    admision=admision,
                    documentacion__isnull=True,
                    nombre_personalizado=org_doc.nombre,
                ).exists()
            ):
                continue

            archivo_admision = (
                AdmisionService._crear_archivo_admision_desde_archivo_organizacion(
                    admision,
                    org_doc,
                    archivo_org,
                    documentacion_admision=documentacion_admision,
                )
            )
            if user:
                archivo_admision.creado_por = user
                archivo_admision.modificado_por = user
                archivo_admision.save(update_fields=["creado_por", "modificado_por"])
            creo_archivos = True

        # Documentacion adicional (personalizada) del legajo (issue #1799 Req 4/1).
        for archivo_org in ArchivoOrganizacion.objects.filter(
            organizacion=organizacion, documentacion__isnull=True
        ):
            if not archivo_org.archivo:
                continue
            if ArchivoAdmision.objects.filter(
                admision=admision, archivo_organizacion_origen=archivo_org
            ).exists():
                continue
            archivo_admision = (
                AdmisionService._crear_archivo_admision_desde_archivo_organizacion(
                    admision, None, archivo_org, documentacion_admision=None
                )
            )
            if user:
                archivo_admision.creado_por = user
                archivo_admision.modificado_por = user
                archivo_admision.save(update_fields=["creado_por", "modificado_por"])
            creo_archivos = True

        if creo_archivos:
            AdmisionService._sincronizar_estado_documental_si_corresponde(admision)

    @staticmethod
    def _existe_archivo_obligatorio_admision(
        *,
        admision,
        doc_obligatorio,
        estado=None,
        requiere_archivo=False,
    ):
        archivo = AdmisionService._obtener_archivo_obligatorio_admision(
            admision=admision,
            doc_obligatorio=doc_obligatorio,
            estado=estado,
        )
        if not archivo:
            return False

        return AdmisionService._archivo_cumple_requisito_documental(
            archivo,
            estado=estado,
            requiere_archivo=requiere_archivo,
        )

    @staticmethod
    def _obtener_archivo_obligatorio_admision(
        *, admision, doc_obligatorio, estado=None
    ):
        archivos_prefetch = getattr(
            doc_obligatorio, "archivos_prefetch_para_admision", None
        )
        if archivos_prefetch is not None:
            for archivo in archivos_prefetch:
                if estado is None or archivo.estado == estado:
                    return archivo
            return None

        filtros = {
            "admision": admision,
            "documentacion": doc_obligatorio,
        }
        if estado is not None:
            filtros["estado"] = estado

        return (
            ArchivoAdmision.objects.filter(**filtros)
            .select_related("admision", "documentacion")
            .order_by("id")
            .first()
        )

    @staticmethod
    def _actualizar_estados_por_cambio_documento(admision, estado_documento):
        """Actualiza estados de admisión basado en cambios de documentos"""
        try:
            if AdmisionService._manejar_rectificacion_documento_admision(
                admision, estado_documento
            ):
                return

            if AdmisionService._bloquea_avance_estado_documental(admision):
                return

            if AdmisionService._sincronizar_estado_documental_si_corresponde(admision):
                return

            AdmisionService._marcar_documentacion_finalizada_si_corresponde(admision)
            AdmisionService._marcar_documentacion_aprobada_si_corresponde(admision)

        except Exception:
            logger.exception(
                "Error en _actualizar_estados_por_cambio_documento",
                extra={
                    "admision_pk": admision.pk,
                    "estado_documento": estado_documento,
                },
            )

    @staticmethod
    def _manejar_rectificacion_documento_admision(admision, estado_documento):

        if estado_documento != "Rectificar":

            return False

        if admision.estado_admision not in [
            "documentacion_finalizada",
            "documentacion_aprobada",
            "documentacion_carga_finalizada",
        ]:

            return True

        if AdmisionService._todos_obligatorios_aceptados(admision):

            return True

        admision.estado_admision = "documentacion_en_proceso"
        admision.save()

        return True

    @staticmethod
    def _bloquea_avance_estado_documental(admision):

        return (
            admision.estado_admision
            in AdmisionService.ESTADOS_BLOQUEO_AVANCE_DOCUMENTAL
        )

    @staticmethod
    def _sincronizar_estado_documental_si_corresponde(admision):
        if AdmisionService._bloquea_avance_estado_documental(admision):
            return False

        estado_actual = getattr(admision, "estado_admision", None)
        if estado_actual not in {
            "convenio_seleccionado",
            "documentacion_en_proceso",
            "documentacion_finalizada",
        }:
            return False

        if not AdmisionService._todos_obligatorios_tienen_archivos(admision):
            return False

        if AdmisionService._todos_obligatorios_aceptados(admision):
            admision.estado_admision = "documentacion_aprobada"
            if admision.estado_id != 2:
                admision.estado_id = 2
            admision.save(update_fields=["estado_admision", "estado"])
            return True

        if estado_actual != "documentacion_finalizada":
            admision.estado_admision = "documentacion_finalizada"
            admision.save(update_fields=["estado_admision"])
            return True

        return False

    @staticmethod
    def bloquea_eliminacion_documental(admision):
        """Indica si la admision ya no admite borrado de documentos adjuntos."""

        return (
            getattr(admision, "estado_admision", None)
            in AdmisionService.ESTADOS_BLOQUEO_ELIMINACION_DOCUMENTAL
        )

    @staticmethod
    def _marcar_documentacion_finalizada_si_corresponde(admision):

        if not AdmisionService._todos_obligatorios_tienen_archivos(admision):

            return False

        if admision.estado_admision != "documentacion_en_proceso":

            return False

        admision.estado_admision = "documentacion_finalizada"
        admision.save()

        return True

    @staticmethod
    def _marcar_documentacion_aprobada_si_corresponde(admision):

        if not AdmisionService._todos_obligatorios_aceptados(admision):

            return False

        if admision.estado_admision != "documentacion_finalizada":

            return False

        admision.estado_admision = "documentacion_aprobada"

        if admision.estado_id != 2:
            admision.estado_id = 2

        admision.save()

        return True

    @staticmethod
    def _todos_obligatorios_tienen_archivos(admision):
        """Verifica que todos los documentos obligatorios tengan archivos cargados"""
        try:
            for (
                doc_obligatorio
            ) in AdmisionService._iter_documentos_obligatorios_admision(admision):
                if not AdmisionService._documento_obligatorio_cumple_requisito(
                    admision=admision,
                    doc_obligatorio=doc_obligatorio,
                    requiere_archivo=True,
                ):
                    return False

            return True

        except Exception:
            logger.exception(
                "Error en _todos_obligatorios_tienen_archivos",
                extra={"admision_pk": admision.pk},
            )
            return False
