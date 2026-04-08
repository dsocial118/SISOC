import logging
import os
from io import BytesIO

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Exists, OuterRef
from django.shortcuts import get_object_or_404
from django.utils import timezone
from pypdf import PdfReader, PdfWriter

from comunicados.models import (
    Comunicado,
    EstadoComunicado,
    SubtipoComunicado,
    TipoComunicado,
)
from comedores.models import Comedor
from pwa.services.mensajes_service import MOBILE_RENDICION_PERMISSION_CODE
from pwa.services.push_service import notify_rendicion_revision_push
from rendicioncuentasmensual.models import DocumentacionAdjunta, RendicionCuentaMensual
from rendicioncuentasmensual.service_helpers import (
    cerrar_archivo_seguro,
    construir_documentacion_para_detalle,
    generar_pdf_desde_imagen,
    generar_pdf_placeholder,
    leer_pdf_documento,
)

logger = logging.getLogger("django")


class RendicionCuentaMensualService:
    MOBILE_MESSAGE_ACTION_PREFIX = "[SISOC_ACCION]"
    MOBILE_MESSAGE_ACTION_SUFFIX = "[/SISOC_ACCION]"
    CATEGORIAS_CON_HISTORIAL_SUBSANACION = {
        DocumentacionAdjunta.CATEGORIA_COMPROBANTES,
        DocumentacionAdjunta.CATEGORIA_OTROS,
    }

    @staticmethod
    def _obtener_comedores_destino_notificacion(rendicion):
        comedor = getattr(rendicion, "comedor", None)
        if not comedor:
            return []

        proyecto_codigo = (getattr(comedor, "codigo_de_proyecto", "") or "").strip()
        if not proyecto_codigo:
            return [comedor]

        filters = {
            "codigo_de_proyecto": proyecto_codigo,
            "deleted_at__isnull": True,
        }
        organizacion_id = getattr(comedor, "organizacion_id", None)
        if organizacion_id:
            filters["organizacion_id"] = organizacion_id
        return list(Comedor.objects.filter(**filters).order_by("nombre", "id"))

    @staticmethod
    def _aplicar_usuario_ultima_modificacion(rendicion, actor):
        if getattr(actor, "is_authenticated", False):
            rendicion.usuario_ultima_modificacion = actor

    @staticmethod
    def _archivar_notificaciones_mobile_rendicion(rendicion):
        if not rendicion or not getattr(rendicion, "id", None):
            return 0
        marker = (
            f"{RendicionCuentaMensualService.MOBILE_MESSAGE_ACTION_PREFIX}"
            f"rendicion_detalle:{rendicion.id}"
            f"{RendicionCuentaMensualService.MOBILE_MESSAGE_ACTION_SUFFIX}"
        )
        return Comunicado.objects.filter(
            tipo=TipoComunicado.EXTERNO,
            subtipo=SubtipoComunicado.COMEDORES,
            estado=EstadoComunicado.PUBLICADO,
            cuerpo__contains=marker,
        ).update(
            estado=EstadoComunicado.ARCHIVADO,
            fecha_publicacion=None,
        )

    @staticmethod
    def _crear_notificacion_mobile_revision_documento(*, documento, actor):
        rendicion = getattr(documento, "rendicion_cuenta_mensual", None)
        if not rendicion or not actor:
            return None
        RendicionCuentaMensualService._archivar_notificaciones_mobile_rendicion(
            rendicion
        )
        if rendicion.estado == RendicionCuentaMensual.ESTADO_FINALIZADA:
            return None
        comedores_destino = (
            RendicionCuentaMensualService._obtener_comedores_destino_notificacion(
                rendicion
            )
        )
        if not comedores_destino:
            return None

        numero_rendicion = getattr(rendicion, "numero_rendicion", None) or rendicion.id
        estado_legible = documento.get_estado_display()
        comedor = getattr(rendicion, "comedor", None)
        proyecto_codigo = (getattr(comedor, "codigo_de_proyecto", "") or "").strip()
        convenio = (getattr(rendicion, "convenio", "") or "").strip()
        proyecto_label = proyecto_codigo or "Sin proyecto"
        convenio_label = convenio or "Sin convenio"
        titulo = (
            f"Proyecto {proyecto_label} | Convenio {convenio_label} | "
            f"Rendici?n {numero_rendicion}: documento {estado_legible.lower()}"
        )

        cuerpo_lineas = [
            (
                "Se actualiz? el estado de un documento de la rendici?n "
                f"{numero_rendicion}."
            ),
            f"Proyecto: {proyecto_label}.",
            f"Convenio: {convenio_label}.",
            f"Documento: {documento.nombre}.",
            f"Estado: {estado_legible}.",
        ]

        if documento.observaciones:
            cuerpo_lineas.append(f"Observaciones: {documento.observaciones}.")

        if rendicion.estado == RendicionCuentaMensual.ESTADO_SUBSANAR:
            cuerpo_lineas.append(
                "La rendición quedó en Presentación a subsanar. "
                "Revisá las observaciones y actualizá la documentación indicada."
            )
        elif rendicion.estado == RendicionCuentaMensual.ESTADO_FINALIZADA:
            cuerpo_lineas.append("La rendición quedó en Presentación finalizada.")
        cuerpo_lineas.append(
            (
                f"{RendicionCuentaMensualService.MOBILE_MESSAGE_ACTION_PREFIX}"
                f"rendicion_detalle:{rendicion.id}"
                f"{RendicionCuentaMensualService.MOBILE_MESSAGE_ACTION_SUFFIX}"
            )
        )

        comunicado = Comunicado.objects.create(
            titulo=titulo,
            cuerpo="\n".join(cuerpo_lineas),
            estado=EstadoComunicado.PUBLICADO,
            tipo=TipoComunicado.EXTERNO,
            subtipo=SubtipoComunicado.COMEDORES,
            para_todos_comedores=False,
            fecha_publicacion=timezone.now(),
            usuario_creador=actor,
            usuario_ultima_modificacion=actor,
        )
        comunicado.comedores.add(*comedores_destino)
        notify_rendicion_revision_push(
            comunicado=comunicado,
            rendicion=rendicion,
            permission_code=MOBILE_RENDICION_PERMISSION_CODE,
            comedor_ids=[comedor_destino.id for comedor_destino in comedores_destino],
        )
        return comunicado

    @staticmethod
    def _get_archivos_adjuntos_data(data):
        return data.get("archivos_adjuntos", data.get("arvhios_adjuntos"))

    @staticmethod
    def _asignar_archivos_adjuntos(rendicion, archivos_adjuntos):
        if archivos_adjuntos is None:
            return

        manager = getattr(rendicion, "archivos_adjuntos", None)
        if hasattr(manager, "set"):
            manager.set(archivos_adjuntos)
            return

        setattr(rendicion, "archivos_adjuntos", archivos_adjuntos)

    @staticmethod
    def _get_project_queryset(comedor):
        queryset = RendicionCuentaMensual.objects.filter(deleted_at__isnull=True)
        proyecto_codigo = (getattr(comedor, "codigo_de_proyecto", "") or "").strip()
        if proyecto_codigo:
            filters = {"comedor__codigo_de_proyecto": proyecto_codigo}
            organizacion_id = getattr(comedor, "organizacion_id", None)
            if organizacion_id:
                filters["comedor__organizacion_id"] = organizacion_id
            return queryset.filter(**filters)
        return queryset.filter(comedor=comedor)

    @staticmethod
    def _documentos_activos_queryset(rendicion):
        return rendicion.archivos_adjuntos.filter(deleted_at__isnull=True).order_by(
            "categoria", "fecha_creacion", "id"
        )

    @staticmethod
    def _documentos_vigentes_queryset(rendicion):
        subsanaciones_activas = DocumentacionAdjunta.objects.filter(
            deleted_at__isnull=True,
            documento_subsanado_id=OuterRef("pk"),
        )
        return (
            RendicionCuentaMensualService._documentos_activos_queryset(rendicion)
            .annotate(tiene_subsanacion_activa=Exists(subsanaciones_activas))
            .filter(tiene_subsanacion_activa=False)
        )

    @staticmethod
    def _sincronizar_flag_documento_adjunto(rendicion):
        tiene_documentos = RendicionCuentaMensualService._documentos_activos_queryset(
            rendicion
        ).exists()
        if rendicion.documento_adjunto != tiene_documentos:
            rendicion.documento_adjunto = tiene_documentos
            rendicion.save(update_fields=["documento_adjunto", "ultima_modificacion"])

    @staticmethod
    def _sincronizar_estado_rendicion_por_documentos(rendicion):
        documentos = list(
            RendicionCuentaMensualService._documentos_vigentes_queryset(rendicion)
        )
        if documentos and all(
            documento.estado == DocumentacionAdjunta.ESTADO_VALIDADO
            for documento in documentos
        ):
            nuevo_estado = RendicionCuentaMensual.ESTADO_FINALIZADA
        elif any(
            documento.estado == DocumentacionAdjunta.ESTADO_SUBSANAR
            for documento in documentos
        ):
            nuevo_estado = RendicionCuentaMensual.ESTADO_SUBSANAR
        else:
            nuevo_estado = RendicionCuentaMensual.ESTADO_REVISION

        if rendicion.estado != nuevo_estado:
            rendicion.estado = nuevo_estado
            rendicion.save(update_fields=["estado", "ultima_modificacion"])
        if nuevo_estado != RendicionCuentaMensual.ESTADO_SUBSANAR:
            RendicionCuentaMensualService._archivar_notificaciones_mobile_rendicion(
                rendicion
            )
        return rendicion

    @staticmethod
    def _validar_numero_y_periodo(
        *,
        comedor,
        convenio,
        numero_rendicion,
        periodo,
        exclude_id=None,
    ):
        periodo_inicio, periodo_fin = periodo
        queryset = RendicionCuentaMensualService._get_project_queryset(comedor)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)

        if queryset.filter(
            convenio=convenio,
            numero_rendicion=numero_rendicion,
        ).exists():
            raise ValidationError(
                {
                    "numero_rendicion": (
                        "Ya existe una rendición con ese número dentro del mismo convenio."
                    )
                }
            )

        if queryset.filter(
            convenio=convenio,
            periodo_inicio__lte=periodo_fin,
            periodo_fin__gte=periodo_inicio,
        ).exists():
            raise ValidationError(
                {
                    "periodo": (
                        "El período no puede repetirse ni solaparse dentro del mismo convenio."
                    )
                }
            )

    @staticmethod
    def _validar_categoria_documental(rendicion, categoria):
        config = DocumentacionAdjunta.get_categoria_config(categoria)
        if not config:
            raise ValidationError(
                {"categoria": "La categoría de documentación es inválida."}
            )

        if (
            not config["multiple"]
            and RendicionCuentaMensualService._documentos_activos_queryset(rendicion)
            .filter(categoria=categoria)
            .exists()
        ):
            raise ValidationError(
                {
                    "categoria": (
                        "Esta categoría admite un único documento activo por rendición."
                    )
                }
            )
        return config

    @staticmethod
    def _obtener_documento_subsanado_para_carga(
        *, rendicion, categoria, documento_subsanado_id
    ):
        documentos_categoria = (
            RendicionCuentaMensualService._documentos_activos_queryset(
                rendicion
            ).filter(categoria=categoria)
        )

        if (
            categoria
            in RendicionCuentaMensualService.CATEGORIAS_CON_HISTORIAL_SUBSANACION
        ):
            if not documento_subsanado_id:
                raise ValidationError(
                    {
                        "detail": (
                            "Debe seleccionar el documento observado que quiere subsanar."
                        )
                    }
                )
            documento = documentos_categoria.filter(id=documento_subsanado_id).first()
            if (
                not documento
                or documento.estado != DocumentacionAdjunta.ESTADO_SUBSANAR
            ):
                raise ValidationError(
                    {
                        "detail": (
                            "El documento seleccionado no está pendiente de subsanación."
                        )
                    }
                )
            if documento.subsanaciones.filter(deleted_at__isnull=True).exists():
                raise ValidationError(
                    {
                        "detail": (
                            "Ese documento ya tiene una subsanación cargada pendiente de revisión."
                        )
                    }
                )
            return documento

        documento = (
            documentos_categoria.filter(estado=DocumentacionAdjunta.ESTADO_SUBSANAR)
            .order_by("fecha_creacion", "id")
            .first()
        )
        if not documento:
            raise ValidationError(
                {
                    "detail": (
                        "No hay un documento observado para reemplazar en esa categoría."
                    )
                }
            )
        return documento

    @staticmethod
    def _validar_carga_documentacion_mobile(
        *, rendicion, categoria, documento_subsanado_id=None
    ):
        config = DocumentacionAdjunta.get_categoria_config(categoria)
        if not config:
            raise ValidationError(
                {"categoria": "La categoría de documentación es inválida."}
            )

        if rendicion.estado == RendicionCuentaMensual.ESTADO_ELABORACION:
            if (
                not config["multiple"]
                and RendicionCuentaMensualService._documentos_activos_queryset(
                    rendicion
                )
                .filter(categoria=categoria)
                .exists()
            ):
                raise ValidationError(
                    {
                        "categoria": (
                            "Esta categoría admite un único documento activo por rendición."
                        )
                    }
                )
            return {"config": config, "documento_subsanado": None}

        if rendicion.estado != RendicionCuentaMensual.ESTADO_SUBSANAR:
            raise ValidationError(
                {
                    "detail": (
                        "La documentación solo puede modificarse en elaboración o durante una subsanación habilitada."
                    )
                }
            )

        documento_subsanado = (
            RendicionCuentaMensualService._obtener_documento_subsanado_para_carga(
                rendicion=rendicion,
                categoria=categoria,
                documento_subsanado_id=documento_subsanado_id,
            )
        )
        return {"config": config, "documento_subsanado": documento_subsanado}

    @staticmethod
    def _validar_rendicion_editable(rendicion):
        if rendicion.estado != RendicionCuentaMensual.ESTADO_ELABORACION:
            raise ValidationError(
                {"detail": ("La documentación solo puede modificarse en elaboración.")}
            )

    @staticmethod
    def obtener_resumen_documentacion(rendicion):
        documentos = list(
            RendicionCuentaMensualService._documentos_activos_queryset(rendicion)
        )
        grouped = {
            item["codigo"]: [] for item in DocumentacionAdjunta.categorias_mobile()
        }
        for documento in documentos:
            grouped.setdefault(documento.categoria, []).append(documento)
        return grouped

    @staticmethod
    def _construir_documentacion_para_detalle(rendicion):
        documentos = list(
            RendicionCuentaMensualService._documentos_activos_queryset(rendicion)
        )
        return construir_documentacion_para_detalle(
            documentos,
            DocumentacionAdjunta.categorias_mobile(),
            RendicionCuentaMensualService.CATEGORIAS_CON_HISTORIAL_SUBSANACION,
        )

    @staticmethod
    def obtener_documentacion_para_detalle(rendicion):
        grouped = RendicionCuentaMensualService._construir_documentacion_para_detalle(
            rendicion
        )
        categorias = []
        for categoria in DocumentacionAdjunta.categorias_mobile():
            categorias.append(
                {
                    **categoria,
                    "archivos": grouped.get(categoria["codigo"], []),
                }
            )
        return categorias

    @staticmethod
    def rendicion_esta_completamente_validada(rendicion):
        return rendicion.estado == RendicionCuentaMensual.ESTADO_FINALIZADA

    @staticmethod
    def obtener_documentos_para_descarga_pdf(rendicion):
        documentos = []
        for (
            categoria
        ) in RendicionCuentaMensualService.obtener_documentacion_para_detalle(
            rendicion
        ):
            for archivo in categoria["archivos"]:
                documentos.append(archivo)
                documentos.extend(getattr(archivo, "subsanaciones_historial", []))
        return documentos

    @staticmethod
    def _generar_pdf_desde_imagen(archivo, nombre):
        return generar_pdf_desde_imagen(archivo, nombre)

    @staticmethod
    def _generar_pdf_placeholder(nombre):
        return generar_pdf_placeholder(nombre)

    @staticmethod
    def generar_pdf_descarga_rendicion(rendicion):
        if not RendicionCuentaMensualService.rendicion_esta_completamente_validada(
            rendicion
        ):
            raise ValidationError(
                {
                    "detail": (
                        "La descarga consolidada solo está disponible cuando la rendición está finalizada."
                    )
                }
            )

        writer = PdfWriter()
        documentos = RendicionCuentaMensualService.obtener_documentos_para_descarga_pdf(
            rendicion
        )
        if not documentos:
            raise ValidationError(
                {"detail": "La rendición no tiene documentación para descargar."}
            )

        for documento in documentos:
            extension = os.path.splitext(documento.archivo.name or "")[1].lower()
            try:
                if extension == ".pdf":
                    reader = leer_pdf_documento(documento.archivo)
                    for page in reader.pages:
                        writer.add_page(page)
                elif extension in {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}:
                    pdf_bytes = RendicionCuentaMensualService._generar_pdf_desde_imagen(
                        documento.archivo, documento.nombre
                    )
                    reader = PdfReader(BytesIO(pdf_bytes))
                    for page in reader.pages:
                        writer.add_page(page)
                else:
                    reader = PdfReader(
                        BytesIO(
                            RendicionCuentaMensualService._generar_pdf_placeholder(
                                documento.nombre
                            )
                        )
                    )
                    for page in reader.pages:
                        writer.add_page(page)
            finally:
                cerrar_archivo_seguro(documento.archivo)

        output = BytesIO()
        writer.write(output)
        output.seek(0)
        return output

    @staticmethod
    def obtener_scope_proyecto(rendicion):
        comedor = getattr(rendicion, "comedor", None)
        organizacion = getattr(comedor, "organizacion", None) if comedor else None
        proyecto_codigo = (getattr(comedor, "codigo_de_proyecto", "") or "").strip()

        related_comedores = []
        if comedor:
            if proyecto_codigo:
                filters = {
                    "codigo_de_proyecto": proyecto_codigo,
                    "deleted_at__isnull": True,
                }
                organizacion_id = getattr(comedor, "organizacion_id", None)
                if organizacion_id:
                    filters["organizacion_id"] = organizacion_id
                related_comedores = list(
                    Comedor.objects.filter(**filters).order_by("nombre")
                )
            else:
                related_comedores = [comedor]

        return {
            "organizacion": organizacion,
            "proyecto_codigo": proyecto_codigo,
            "comedores_relacionados": related_comedores,
        }

    @staticmethod
    def validar_documentacion_obligatoria(rendicion):
        grouped = {}
        for documento in RendicionCuentaMensualService._documentos_vigentes_queryset(
            rendicion
        ):
            grouped.setdefault(documento.categoria, []).append(documento)
        faltantes = []
        for categoria in DocumentacionAdjunta.categorias_mobile():
            if categoria["required"] and not grouped.get(categoria["codigo"]):
                faltantes.append(categoria["label"])
        if faltantes:
            raise ValidationError(
                {
                    "detail": (
                        "Falta cargar documentación obligatoria: "
                        + ", ".join(faltantes)
                        + "."
                    )
                }
            )

    @staticmethod
    @transaction.atomic
    def crear_rendicion_mobile(*, comedor, data, actor=None):
        convenio = (data.get("convenio") or "").strip()
        numero_rendicion = data.get("numero_rendicion")
        periodo_inicio = data.get("periodo_inicio")
        periodo_fin = data.get("periodo_fin")
        observaciones = (data.get("observaciones") or "").strip()

        RendicionCuentaMensualService._validar_numero_y_periodo(
            comedor=comedor,
            convenio=convenio,
            numero_rendicion=numero_rendicion,
            periodo=(periodo_inicio, periodo_fin),
        )

        return RendicionCuentaMensual.objects.create(
            comedor=comedor,
            mes=periodo_inicio.month,
            anio=periodo_inicio.year,
            convenio=convenio,
            numero_rendicion=numero_rendicion,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
            estado=RendicionCuentaMensual.ESTADO_ELABORACION,
            observaciones=observaciones or None,
            documento_adjunto=False,
            usuario_creador=(
                actor if getattr(actor, "is_authenticated", False) else None
            ),
            usuario_ultima_modificacion=(
                actor if getattr(actor, "is_authenticated", False) else None
            ),
        )

    @staticmethod
    @transaction.atomic
    def adjuntar_documentacion_mobile(
        *,
        rendicion,
        categoria,
        documento_data,
        actor=None,
        documento_subsanado_id=None,
    ):
        archivo = documento_data["archivo"]
        nombre = documento_data["nombre"]
        validacion = RendicionCuentaMensualService._validar_carga_documentacion_mobile(
            rendicion=rendicion,
            categoria=categoria,
            documento_subsanado_id=documento_subsanado_id,
        )
        documento_subsanado = validacion["documento_subsanado"]

        if (
            documento_subsanado
            and categoria
            not in RendicionCuentaMensualService.CATEGORIAS_CON_HISTORIAL_SUBSANACION
        ):
            documento_subsanado.delete()

        documento = DocumentacionAdjunta.objects.create(
            nombre=nombre,
            categoria=categoria,
            estado=DocumentacionAdjunta.ESTADO_PRESENTADO,
            archivo=archivo,
            rendicion_cuenta_mensual=rendicion,
            documento_subsanado=documento_subsanado,
        )
        RendicionCuentaMensualService._aplicar_usuario_ultima_modificacion(
            rendicion, actor
        )
        if getattr(actor, "is_authenticated", False):
            rendicion.save(
                update_fields=["usuario_ultima_modificacion", "ultima_modificacion"]
            )
        RendicionCuentaMensualService._sincronizar_flag_documento_adjunto(rendicion)
        return documento

    @staticmethod
    @transaction.atomic
    def eliminar_documentacion_mobile(*, rendicion, documento, actor=None):
        RendicionCuentaMensualService._validar_rendicion_editable(rendicion)
        if documento.rendicion_cuenta_mensual_id != rendicion.id:
            raise ValidationError(
                {"detail": "El documento no pertenece a la rendición."}
            )
        documento.delete()
        RendicionCuentaMensualService._aplicar_usuario_ultima_modificacion(
            rendicion, actor
        )
        if getattr(actor, "is_authenticated", False):
            rendicion.save(
                update_fields=["usuario_ultima_modificacion", "ultima_modificacion"]
            )
        RendicionCuentaMensualService._sincronizar_flag_documento_adjunto(rendicion)

    @staticmethod
    @transaction.atomic
    def presentar_rendicion_mobile(rendicion, actor=None):
        RendicionCuentaMensualService.validar_documentacion_obligatoria(rendicion)
        RendicionCuentaMensualService._sincronizar_flag_documento_adjunto(rendicion)
        documentos_vigentes = list(
            RendicionCuentaMensualService._documentos_vigentes_queryset(rendicion)
        )
        if any(
            documento.estado == DocumentacionAdjunta.ESTADO_SUBSANAR
            for documento in documentos_vigentes
        ):
            raise ValidationError(
                {
                    "detail": (
                        "Todavía hay documentación observada pendiente de subsanar."
                    )
                }
            )
        rendicion.estado = RendicionCuentaMensual.ESTADO_REVISION
        RendicionCuentaMensualService._aplicar_usuario_ultima_modificacion(
            rendicion, actor
        )
        update_fields = ["estado", "ultima_modificacion"]
        if getattr(actor, "is_authenticated", False):
            update_fields.append("usuario_ultima_modificacion")
        rendicion.save(update_fields=update_fields)
        RendicionCuentaMensualService._archivar_notificaciones_mobile_rendicion(
            rendicion
        )
        return rendicion

    @staticmethod
    @transaction.atomic
    def actualizar_estado_documento_revision(
        *, documento, estado, observaciones=None, actor=None
    ):
        if estado not in (
            DocumentacionAdjunta.ESTADO_VALIDADO,
            DocumentacionAdjunta.ESTADO_SUBSANAR,
        ):
            raise ValidationError({"estado": "El estado seleccionado es inválido."})

        if documento.estado != DocumentacionAdjunta.ESTADO_PRESENTADO:
            raise ValidationError(
                {"detail": ("Solo se pueden revisar documentos en estado Presentado.")}
            )

        rendicion = documento.rendicion_cuenta_mensual
        if not rendicion or rendicion.estado not in (
            RendicionCuentaMensual.ESTADO_REVISION,
            RendicionCuentaMensual.ESTADO_SUBSANAR,
        ):
            raise ValidationError(
                {
                    "detail": (
                        "La rendición no admite revisión de documentos en su estado actual."
                    )
                }
            )

        observaciones_limpias = (observaciones or "").strip()
        if estado == DocumentacionAdjunta.ESTADO_SUBSANAR and not observaciones_limpias:
            raise ValidationError(
                {
                    "observaciones": (
                        "Debe ingresar observaciones para enviar el documento a subsanar."
                    )
                }
            )

        documento.estado = estado
        documento.observaciones = (
            observaciones_limpias or None
            if estado == DocumentacionAdjunta.ESTADO_SUBSANAR
            else None
        )
        documento.save(update_fields=["estado", "observaciones", "ultima_modificacion"])
        RendicionCuentaMensualService._aplicar_usuario_ultima_modificacion(
            rendicion, actor
        )
        if getattr(actor, "is_authenticated", False):
            rendicion.save(
                update_fields=["usuario_ultima_modificacion", "ultima_modificacion"]
            )
        RendicionCuentaMensualService._sincronizar_estado_rendicion_por_documentos(
            rendicion
        )
        RendicionCuentaMensualService._crear_notificacion_mobile_revision_documento(
            documento=documento,
            actor=actor,
        )
        return documento

    @staticmethod
    @transaction.atomic
    def eliminar_rendicion_mobile(rendicion):
        RendicionCuentaMensualService._validar_rendicion_editable(rendicion)
        rendicion.delete()

    @staticmethod
    def crear_rendicion_cuenta_mensual(comedor, data):
        try:
            archivos_adjuntos = (
                RendicionCuentaMensualService._get_archivos_adjuntos_data(data)
            )
            rendicion = RendicionCuentaMensual.objects.create(
                comedor=comedor,
                mes=data.get("mes"),
                anio=data.get("anio"),
                convenio=data.get("convenio"),
                numero_rendicion=data.get("numero_rendicion"),
                periodo_inicio=data.get("periodo_inicio"),
                periodo_fin=data.get("periodo_fin"),
                estado=data.get("estado") or RendicionCuentaMensual.ESTADO_ELABORACION,
                documento_adjunto=data.get("documento_adjunto"),
                observaciones=data.get("observaciones"),
            )
            RendicionCuentaMensualService._asignar_archivos_adjuntos(
                rendicion, archivos_adjuntos
            )
            return rendicion
        except Exception:
            logger.exception(
                "Error en RendicionCuentaMensualService.crear_rendicion_cuenta_mensual",
                extra={"comedor_pk": getattr(comedor, "pk", None)},
            )
            raise

    @staticmethod
    def actualizar_rendicion_cuenta_mensual(rendicion, data):
        try:
            archivos_adjuntos = (
                RendicionCuentaMensualService._get_archivos_adjuntos_data(data)
            )
            rendicion.mes = data.get("mes")
            rendicion.anio = data.get("anio")
            rendicion.convenio = data.get("convenio")
            rendicion.numero_rendicion = data.get("numero_rendicion")
            rendicion.periodo_inicio = data.get("periodo_inicio")
            rendicion.periodo_fin = data.get("periodo_fin")
            rendicion.estado = (
                data.get("estado") or RendicionCuentaMensual.ESTADO_ELABORACION
            )
            rendicion.documento_adjunto = data.get("documento_adjunto")
            rendicion.observaciones = data.get("observaciones")
            RendicionCuentaMensualService._asignar_archivos_adjuntos(
                rendicion, archivos_adjuntos
            )
            rendicion.save()
            return rendicion
        except Exception:
            logger.exception(
                "Error en RendicionCuentaMensualService.actualizar_rendicion_cuenta_mensual",
                extra={"rendicion_pk": getattr(rendicion, "pk", None)},
            )
            raise

    @staticmethod
    def eliminar_rendicion_cuenta_mensual(rendicion):
        try:
            rendicion.delete()
        except Exception:
            logger.exception(
                "Error en RendicionCuentaMensualService.eliminar_rendicion_cuenta_mensual",
                extra={"rendicion_pk": getattr(rendicion, "pk", None)},
            )
            raise

    @staticmethod
    def obtener_rendiciones_cuentas_mensuales(comedor):
        try:
            return RendicionCuentaMensualService._get_project_queryset(comedor)
        except Exception:
            logger.exception(
                "Error en RendicionCuentaMensualService.obtener_rendiciones_cuentas_mensuales",
                extra={"comedor_pk": getattr(comedor, "pk", None)},
            )
            raise

    @staticmethod
    def obtener_todas_rendiciones_cuentas_mensuales():
        try:
            return (
                RendicionCuentaMensual.objects.filter(deleted_at__isnull=True)
                .select_related("comedor")
                .order_by("-ultima_modificacion", "-id")
            )
        except Exception:
            logger.exception(
                "Error en RendicionCuentaMensualService.obtener_todas_rendiciones_cuentas_mensuales"
            )
            raise

    @staticmethod
    def obtener_rendicion_cuenta_mensual(id_enviado):
        try:
            return get_object_or_404(RendicionCuentaMensual, pk=id_enviado)
        except Exception:
            logger.exception(
                "Error en RendicionCuentaMensualService.obtener_rendicion_cuenta_mensual para %s",
                id_enviado,
            )
            raise

    @staticmethod
    def cantidad_rendiciones_cuentas_mensuales(comedor):
        try:
            return RendicionCuentaMensualService._get_project_queryset(comedor).count()
        except Exception:
            logger.exception(
                "Error en RendicionCuentaMensualService.cantidad_rendiciones_cuentas_mensuales",
                extra={"comedor_pk": getattr(comedor, "pk", None)},
            )
            raise
