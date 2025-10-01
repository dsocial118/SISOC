from django.utils.http import url_has_allowed_host_and_scheme
from django.shortcuts import redirect
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.db import models
from django.template.loader import render_to_string, get_template
from weasyprint import HTML
import os
from django.conf import settings
from django.db.models import Q
import logging
from io import BytesIO
import tempfile

from django.core.files.base import ContentFile
from django.utils.html import strip_tags
from django.utils.text import slugify
from docx import Document
from htmldocx import HtmlToDocx

logger = logging.getLogger("django")

from admisiones.models.admisiones import (
    FormularioProyectoDisposicion,
    FormularioProyectoDeConvenio,
    DocumentosExpediente,
    Admision,
    ArchivoAdmision,
    Documentacion,
    InformeTecnico,
    InformeComplementario,
)
from admisiones.forms.admisiones_forms import (
    LegalesNumIFForm,
    LegalesRectificarForm,
    ProyectoDisposicionForm,
    ProyectoConvenioForm,
    DocumentosExpedienteForm,
    ConvenioNumIFFORM,
    DisposicionNumIFFORM,
    IntervencionJuridicosForm,
    InformeSGAForm,
    ConvenioForm,
    DisposicionForm,
    ReinicioExpedienteForm,
)


class LegalesService:
    @staticmethod
    def enviar_a_rectificar(request, admision):
        try:
            form = LegalesRectificarForm(request.POST)
            if form.is_valid():
                observaciones = form.cleaned_data["observaciones"]
                cambios = False

                if admision.estado_id != 3:
                    admision.estado_id = 3
                    cambios = True

                if admision.estado_legales != "A Rectificar":
                    admision.estado_legales = "A Rectificar"
                    cambios = True

                if admision.observaciones != observaciones:
                    admision.observaciones = observaciones
                    cambios = True

                if cambios:
                    admision.save()

                messages.success(request, "Enviado a rectificar con éxito.")
            else:
                messages.error(request, "Error al enviar a rectificar.")
            return redirect("admisiones_legales_ver", pk=admision.pk)
        except Exception:
            logger.exception(
                "Error en enviar_a_rectificar",
                extra={"admision_pk": admision.pk},
            )
            messages.error(request, "Error inesperado al enviar a rectificar.")
            return redirect("admisiones_legales_ver", pk=admision.pk)

    @staticmethod
    def guardar_legales_num_if(request, admision):
        try:
            form = LegalesNumIFForm(request.POST, instance=admision)
            if form.is_valid():
                form.save()
                messages.success(request, "Número de IF guardado correctamente.")
            else:
                messages.error(request, "Error al guardar el número de IF.")
            if url_has_allowed_host_and_scheme(
                request.path_info, allowed_hosts={request.get_host()}
            ):
                return redirect(request.path_info)
            else:
                return redirect("admisiones_legales_ver", pk=admision.pk)
        except Exception:
            logger.exception(
                "Error en guardar_legales_num_if",
                extra={"admision_pk": admision.pk},
            )
            messages.error(request, "Error inesperado al guardar el número de IF.")
            if url_has_allowed_host_and_scheme(
                request.path_info, allowed_hosts={request.get_host()}
            ):
                return redirect(request.path_info)
            else:
                return redirect("admisiones_legales_ver", pk=admision.pk)

    @staticmethod
    def guardar_intervencion_juridicos(request, admision):
        try:
            form = IntervencionJuridicosForm(request.POST, instance=admision)
            if form.is_valid():
                form.save()
                messages.success(
                    request, "Intervención Jurídicos guardada correctamente."
                )
            else:
                messages.error(request, "Error al guardar Intervención Jurídicos.")
        except Exception:
            logger.exception(
                "Error en guardar_intervencion_juridicos",
                extra={"admision_pk": admision.pk},
            )
            messages.error(
                request, "Error inesperado al guardar Intervención Jurídicos."
            )
        return redirect("admisiones_legales_ver", pk=admision.pk)

    @staticmethod
    def guardar_informe_sga(request, admision):
        try:
            admision.informe_sga = not admision.informe_sga
            admision.save(update_fields=["informe_sga"])
            messages.success(
                request,
                f"Informe SGA {'Aceptado' if admision.informe_sga else 'No aceptado'}.",
            )
        except Exception:
            logger.exception(
                "Error en guardar_informe_sga", extra={"admision_pk": admision.pk}
            )
            messages.error(
                request, "Error inesperado al guardar el estado del Informe SGA."
            )
        return redirect("admisiones_legales_ver", pk=admision.pk)

    @staticmethod
    def guardar_convenio(request, admision):
        try:
            form = ConvenioForm(request.POST, request.FILES, instance=admision)
            if form.is_valid():
                form.save()
                messages.success(request, "Convenio guardado correctamente.")
            else:
                logger.error("Errores en ConvenioForm: %s", form.errors)
                messages.error(request, "Error al guardar el Convenio.")
            return redirect("admisiones_legales_ver", pk=admision.pk)
        except Exception:
            logger.exception(
                "Error en guardar_convenio", extra={"admision_pk": admision.pk}
            )
            messages.error(request, "Error inesperado al guardar el Convenio.")
            return redirect("admisiones_legales_ver", pk=admision.pk)

    @staticmethod
    def guardar_disposicion(request, admision):
        try:
            form = DisposicionForm(request.POST, request.FILES, instance=admision)
            if form.is_valid():
                form.save()
                messages.success(request, "Disposición guardada correctamente.")
            else:
                logger.error("Errores en DisposicionForm: %s", form.errors)
                messages.error(request, "Error al guardar Disposición.")
            return redirect("admisiones_legales_ver", pk=admision.pk)
        except Exception:
            logger.exception(
                "Error en guardar_disposicion", extra={"admision_pk": admision.pk}
            )
            messages.error(request, "Error inesperado al guardar Disposición.")
            return redirect("admisiones_legales_ver", pk=admision.pk)

    @staticmethod
    def guardar_convenio_num_if(request, admision):
        try:
            formulario = admision.admisiones_proyecto_convenio.first()
            if formulario is None:
                formulario = FormularioProyectoDeConvenio(admision=admision)
            form = ConvenioNumIFFORM(request.POST, instance=formulario)
            if form.is_valid():
                convenio = form.save(commit=False)
                convenio.admision = admision
                if (
                    not getattr(convenio, "creado_por", None)
                    and request.user.is_authenticated
                ):
                    convenio.creado_por = request.user
                convenio.save()
                messages.success(
                    request, "Número IF de Proyecto de Convenio guardado correctamente."
                )
            else:
                messages.error(
                    request, "Error al guardar el número IF de Proyecto de Convenio."
                )
            return redirect(request.path_info)
        except Exception:
            logger.exception(
                "Error en guardar_convenio_num_if",
                extra={"admision_pk": admision.pk},
            )
            messages.error(
                request,
                "Error inesperado al guardar el número IF de Proyecto de Convenio.",
            )
            return redirect(request.path_info)

    @staticmethod
    def guardar_reinicio_expediente(request, admision):
        try:
            form = ReinicioExpedienteForm(request.POST, instance=admision)
            if form.is_valid():
                reinicio = form.save(commit=False)
                reinicio.enviada_a_archivo = True
                reinicio.estado_legales = "Archivado"
                reinicio.save(
                    update_fields=[
                        "observaciones_reinicio_expediente",
                        "enviada_a_archivo",
                    ]
                )
                messages.success(
                    request,
                    "Reinicio de expediente guardado y enviado a archivo correctamente.",
                )
            else:
                messages.error(request, "Error al guardar el reinicio de expediente.")
            return redirect(request.path_info)
        except Exception:
            logger.exception(
                "Error en guardar_reinicio_expediente",
                extra={"admision_pk": admision.pk},
            )
            messages.error(
                request, "Error inesperado al guardar el reinicio de expediente."
            )
            return redirect(request.path_info)

    @staticmethod
    def guardar_dispo_num_if(request, admision):
        try:
            formulario = admision.admisiones_proyecto_disposicion.first()
            if formulario is None:
                formulario = FormularioProyectoDisposicion(admision=admision)
            form = DisposicionNumIFFORM(request.POST, instance=formulario)
            if form.is_valid():
                disposicion = form.save(commit=False)
                disposicion.admision = admision
                if (
                    not getattr(disposicion, "creado_por", None)
                    and request.user.is_authenticated
                ):
                    disposicion.creado_por = request.user
                disposicion.save()
                messages.success(
                    request,
                    "Número IF de Proyecto de Disposición guardado correctamente.",
                )
            else:
                messages.error(
                    request, "Error al guardar el número IF de Proyecto de Disposición."
                )
            return redirect(request.path_info)
        except Exception:
            logger.exception(
                "Error en guardar_dispo_num_if",
                extra={"admision_pk": admision.pk},
            )
            messages.error(
                request,
                "Error inesperado al guardar el número IF de Proyecto de Disposición.",
            )
            return redirect(request.path_info)

    @staticmethod
    def validar_juridicos(request, admision):
        try:
            reso_completo = FormularioProyectoDisposicion.objects.filter(
                admision=admision
            ).exists()
            proyecto_completo = FormularioProyectoDeConvenio.objects.filter(
                admision=admision
            ).exists()

            condiciones_validas = (
                reso_completo
                and proyecto_completo
                and (
                    admision.observaciones is None
                    or admision.observaciones.strip() == ""
                )
                and admision.estado_legales != "A Rectificar"
                and admision.legales_num_if not in [None, ""]
            )

            if condiciones_validas:
                admision.estado_legales = "Pendiente de Validacion"
                admision.save()
                messages.success(
                    request, "Estado cambiado a 'Pendiente de Validacion'."
                )
            else:
                messages.error(
                    request,
                    "No se puede validar: asegúrese de completar ambos formularios y agregar el Número IF.",
                )

            if url_has_allowed_host_and_scheme(
                request.path_info, allowed_hosts={request.get_host()}
            ):
                return redirect(request.path_info)
            else:
                return redirect("admisiones_legales_ver", pk=admision.pk)
        except Exception:
            logger.exception(
                "Error en validar_juridicos",
                extra={"admision_pk": admision.pk},
            )
            messages.error(request, "Error inesperado al validar jurídicos.")
            if url_has_allowed_host_and_scheme(
                request.path_info, allowed_hosts={request.get_host()}
            ):
                return redirect(request.path_info)
            else:
                return redirect("admisiones_legales_ver", pk=admision.pk)

    @staticmethod
    def guardar_formulario_reso(request, admision):
        try:
            formulario_existente = FormularioProyectoDisposicion.objects.filter(
                admision=admision
            ).first()
            form = ProyectoDisposicionForm(request.POST, instance=formulario_existente)

            if not form.is_valid():
                messages.error(request, "Error al guardar el formulario RESO.")
                return redirect("admisiones_legales_ver", pk=admision.pk)

            nuevo_formulario = form.save(commit=False)
            nuevo_formulario.admision = admision
            if request.user.is_authenticated:
                nuevo_formulario.creado_por = request.user
            nuevo_formulario.save()

            informe = (
                InformeTecnico.objects.filter(admision=admision).order_by("-id").first()
            )

            pdf_template_name = (
                "admisiones/pdf_dispo_incorporacion.html"
                if nuevo_formulario.tipo == "incorporacion"
                else "admisiones/pdf_dispo_renovacion.html"
            )
            docx_template_name = pdf_template_name.replace("pdf_", "docx_")

            context = {
                "admision": admision,
                "formulario": nuevo_formulario,
                "informe": informe,
            }

            html_pdf = render_to_string(pdf_template_name, context)
            if not html_pdf.strip():
                raise ValueError(
                    f"El template {pdf_template_name} devolvió contenido vacío."
                )

            html_docx = html_pdf
            try:
                get_template(docx_template_name)
                html_docx_candidate = render_to_string(docx_template_name, context)
                if html_docx_candidate.strip():
                    html_docx = html_docx_candidate
            except Exception:
                pass

            base_url = str(
                getattr(settings, "STATIC_ROOT", "")
                or getattr(settings, "BASE_DIR", "")
                or "."
            )
            pdf_bytes = HTML(string=html_pdf, base_url=base_url).write_pdf()
            if not pdf_bytes:
                raise ValueError(
                    "WeasyPrint no devolvió contenido para el PDF generado."
                )
            pdf_content = ContentFile(pdf_bytes)

            docx_content = None
            try:
                doc = Document()
                HtmlToDocx().add_html_to_document(html_docx, doc)
                buffer = BytesIO()
                doc.save(buffer)
                buffer.seek(0)
                docx_bytes = buffer.getvalue()
                if not docx_bytes:
                    raise ValueError("htmldocx devolvió contenido vacío.")
                docx_content = ContentFile(docx_bytes)
            except Exception as docx_exc:
                logger.warning(
                    "Falla al generar DOCX para formulario RESO",
                    exc_info=docx_exc,
                    extra={
                        "admision_pk": admision.pk,
                        "formulario_pk": getattr(nuevo_formulario, "pk", None),
                    },
                )
                try:
                    fallback_doc = Document()
                    fallback_text = strip_tags(html_docx)
                    for line in filter(
                        None,
                        (segment.strip() for segment in fallback_text.splitlines()),
                    ):
                        fallback_doc.add_paragraph(line)
                    buffer = BytesIO()
                    fallback_doc.save(buffer)
                    buffer.seek(0)
                    docx_bytes = buffer.getvalue()
                    if docx_bytes:
                        docx_content = ContentFile(docx_bytes)
                    else:
                        logger.error(
                            "El fallback de DOCX para formulario RESO devolvió contenido vacío.",
                            extra={
                                "admision_pk": admision.pk,
                                "formulario_pk": getattr(nuevo_formulario, "pk", None),
                            },
                        )
                except Exception as fallback_exc:
                    logger.error(
                        "No se pudo generar el fallback DOCX para formulario RESO",
                        exc_info=fallback_exc,
                        extra={
                            "admision_pk": admision.pk,
                            "formulario_pk": getattr(nuevo_formulario, "pk", None),
                        },
                    )

            base_filename = (
                slugify(
                    f"{nuevo_formulario.tipo or 'disposicion'}-{admision.id}-{nuevo_formulario.id}"
                )
                or f"disposicion-{admision.id}-{nuevo_formulario.id}"
            )

            if nuevo_formulario.archivo:
                nuevo_formulario.archivo.delete(save=False)
            nuevo_formulario.archivo.save(
                f"{base_filename}.pdf", pdf_content, save=False
            )

            update_fields = ["archivo"]
            if docx_content:
                if nuevo_formulario.archivo_docx:
                    nuevo_formulario.archivo_docx.delete(save=False)
                nuevo_formulario.archivo_docx.save(
                    f"{base_filename}.docx", docx_content, save=False
                )
                update_fields.append("archivo_docx")

            nuevo_formulario.save(update_fields=update_fields)

            messages.success(
                request, "Formulario guardado y documentos generados correctamente."
            )
            return redirect("admisiones_legales_ver", pk=admision.pk)
        except Exception:
            html_dump_path = None
            try:
                if "html_pdf" in locals() and html_pdf:
                    with tempfile.NamedTemporaryFile(
                        mode="w", encoding="utf-8", suffix=".html", delete=False
                    ) as temp_file:
                        temp_file.write(html_pdf)
                        html_dump_path = temp_file.name
            except Exception as dump_exc:
                logger.error(
                    "No se pudo escribir el HTML temporal para formulario RESO",
                    exc_info=dump_exc,
                    extra={"admision_pk": admision.pk},
                )

            extra = {"admision_pk": admision.pk}
            if "nuevo_formulario" in locals():
                extra["formulario_pk"] = getattr(nuevo_formulario, "pk", None)
            if html_dump_path:
                extra["html_dump_path"] = html_dump_path

            logger.exception("Error en guardar_formulario_reso", extra=extra)
            messages.error(request, "Error inesperado al guardar el formulario RESO.")
            return redirect("admisiones_legales_ver", pk=admision.pk)

    @staticmethod
    def guardar_formulario_proyecto_convenio(request, admision):
        try:
            formulario_existente = FormularioProyectoDeConvenio.objects.filter(
                admision=admision
            ).first()
            form = ProyectoConvenioForm(request.POST, instance=formulario_existente)

            if not form.is_valid():
                messages.error(
                    request, "Error al guardar el formulario Proyecto de Convenio."
                )
                return redirect(request.path_info)

            nuevo_formulario = form.save(commit=False)
            nuevo_formulario.admision = admision
            if request.user.is_authenticated:
                nuevo_formulario.creado_por = request.user
            nuevo_formulario.save()

            context = {"admision": admision, "formulario": nuevo_formulario}

            pdf_template_name = "admisiones/pdf_convenio.html"
            docx_template_name = "admisiones/docx_convenio.html"

            html_pdf = render_to_string(pdf_template_name, context)
            if not html_pdf.strip():
                raise ValueError(
                    f"El template {pdf_template_name} devolvió contenido vacío."
                )

            html_docx = html_pdf
            try:
                get_template(docx_template_name)
                html_docx_candidate = render_to_string(docx_template_name, context)
                if html_docx_candidate.strip():
                    html_docx = html_docx_candidate
            except Exception:
                pass

            base_url = str(
                getattr(settings, "STATIC_ROOT", "")
                or getattr(settings, "BASE_DIR", "")
                or "."
            )
            pdf_bytes = HTML(string=html_pdf, base_url=base_url).write_pdf()
            if not pdf_bytes:
                raise ValueError(
                    "WeasyPrint no devolvió contenido para el PDF generado."
                )
            pdf_content = ContentFile(pdf_bytes)

            docx_content = None
            try:
                doc = Document()
                HtmlToDocx().add_html_to_document(html_docx, doc)
                buffer = BytesIO()
                doc.save(buffer)
                buffer.seek(0)
                docx_bytes = buffer.getvalue()
                if not docx_bytes:
                    raise ValueError("htmldocx devolvió contenido vacío.")
                docx_content = ContentFile(docx_bytes)
            except Exception as docx_exc:
                logger.warning(
                    "Falla al generar DOCX para formulario de Convenio",
                    exc_info=docx_exc,
                    extra={
                        "admision_pk": admision.pk,
                        "formulario_pk": getattr(nuevo_formulario, "pk", None),
                    },
                )
                try:
                    fallback_doc = Document()
                    fallback_text = strip_tags(html_docx)
                    for line in filter(
                        None,
                        (segment.strip() for segment in fallback_text.splitlines()),
                    ):
                        fallback_doc.add_paragraph(line)
                    buffer = BytesIO()
                    fallback_doc.save(buffer)
                    buffer.seek(0)
                    docx_bytes = buffer.getvalue()
                    if docx_bytes:
                        docx_content = ContentFile(docx_bytes)
                    else:
                        logger.error(
                            "El fallback de DOCX para formulario de Convenio devolvió contenido vacío.",
                            extra={
                                "admision_pk": admision.pk,
                                "formulario_pk": getattr(nuevo_formulario, "pk", None),
                            },
                        )
                except Exception as fallback_exc:
                    logger.error(
                        "No se pudo generar el fallback DOCX para formulario de Convenio",
                        exc_info=fallback_exc,
                        extra={
                            "admision_pk": admision.pk,
                            "formulario_pk": getattr(nuevo_formulario, "pk", None),
                        },
                    )

            base_filename = (
                slugify(f"convenio-{admision.id}-{nuevo_formulario.id}")
                or f"convenio-{admision.id}-{nuevo_formulario.id}"
            )

            if nuevo_formulario.archivo:
                nuevo_formulario.archivo.delete(save=False)
            nuevo_formulario.archivo.save(
                f"{base_filename}.pdf", pdf_content, save=False
            )

            update_fields = ["archivo"]
            if docx_content:
                if nuevo_formulario.archivo_docx:
                    nuevo_formulario.archivo_docx.delete(save=False)
                nuevo_formulario.archivo_docx.save(
                    f"{base_filename}.docx", docx_content, save=False
                )
                update_fields.append("archivo_docx")

            nuevo_formulario.save(update_fields=update_fields)

            messages.success(
                request, "Formulario guardado y documentos generados correctamente."
            )
            return redirect(request.path_info)
        except Exception:
            html_dump_path = None
            try:
                if "html_pdf" in locals() and html_pdf:
                    with tempfile.NamedTemporaryFile(
                        mode="w", encoding="utf-8", suffix=".html", delete=False
                    ) as temp_file:
                        temp_file.write(html_pdf)
                        html_dump_path = temp_file.name
            except Exception as dump_exc:
                logger.error(
                    "No se pudo escribir el HTML temporal para formulario de Convenio",
                    exc_info=dump_exc,
                    extra={"admision_pk": admision.pk},
                )

            extra = {"admision_pk": admision.pk}
            if "nuevo_formulario" in locals():
                extra["formulario_pk"] = getattr(nuevo_formulario, "pk", None)
            if html_dump_path:
                extra["html_dump_path"] = html_dump_path

            logger.exception(
                "Error en guardar_formulario_proyecto_convenio", extra=extra
            )
            messages.error(
                request,
                "Error inesperado al guardar el formulario Proyecto de Convenio.",
            )
            return redirect(request.path_info)

    @staticmethod
    def guardar_documento_expediente(request, admision):
        try:
            form = DocumentosExpedienteForm(request.POST, request.FILES)
            if form.is_valid():
                documento = form.save(commit=False)
                documento.admision = admision
                documento.save()

                cambio_estado = {
                    "Informe SGA": "Informe SGA Generado",
                    "Disposición": "Disposición Generada",
                    "Firma Convenio": "Convenio Firmado",
                    "Numero CONV": "Finalizado",
                }

                tipo = documento.tipo
                nuevo_estado = cambio_estado.get(tipo)

                if nuevo_estado:
                    admision.estado_legales = nuevo_estado
                    admision.save(update_fields=["estado_legales"])

                messages.success(request, "Se ha cargado con éxito.")
            else:
                messages.error(request, "Error al guardar.")
                logger.error(
                    "Error al guardar documento de expediente: %s", form.errors
                )

            return redirect(request.path_info)
        except Exception:
            logger.exception(
                "Error en guardar_documento_expediente",
                extra={"admision_pk": admision.pk},
            )
            messages.error(
                request, "Error inesperado al guardar el documento de expediente."
            )
            return redirect(request.path_info)

    @staticmethod
    def get_admisiones_legales_filtradas(query=""):
        try:
            queryset = Admision.objects.filter(enviado_legales=True).select_related(
                "comedor", "tipo_convenio"
            )

            if query:
                query = query.strip().lower()
                queryset = queryset.filter(
                    Q(comedor__nombre__icontains=query)
                    | Q(tipo_convenio__nombre__icontains=query)
                    | Q(num_expediente__icontains=query)
                    | Q(num_if__icontains=query)
                    | Q(estado_legales__icontains=query)
                )

            return queryset
        except Exception:
            logger.exception("Error en get_admisiones_legales_filtradas")
            return Admision.objects.none()

    @staticmethod
    def procesar_post_legales(request, admision):
        try:
            if "btnLegalesNumIF" in request.POST:
                return LegalesService.guardar_legales_num_if(request, admision)

            if "BtnIntervencionJuridicos" in request.POST:
                return LegalesService.guardar_intervencion_juridicos(request, admision)

            if "BtnInformeSGA" in request.POST:
                return LegalesService.guardar_informe_sga(request, admision)

            if "btnConvenio" in request.POST:
                return LegalesService.guardar_convenio(request, admision)

            if "btnDisposicion" in request.POST:
                return LegalesService.guardar_disposicion(request, admision)

            if "btnConvenioNumIF" in request.POST:
                return LegalesService.guardar_convenio_num_if(request, admision)

            if "btnDispoNumIF" in request.POST:
                return LegalesService.guardar_dispo_num_if(request, admision)

            if "btnReinicioExpediente" in request.POST:
                return LegalesService.guardar_reinicio_expediente(request, admision)

            if "ValidacionJuridicos" in request.POST:
                return LegalesService.validar_juridicos(request, admision)

            if "btnRESO" in request.POST:
                return LegalesService.guardar_formulario_reso(request, admision)

            if "btnProyectoConvenio" in request.POST:
                return LegalesService.guardar_formulario_proyecto_convenio(
                    request, admision
                )

            if "btnObservaciones" in request.POST:
                return LegalesService.enviar_a_rectificar(request, admision)

            if "btnDocumentoExpediente" in request.POST:
                return LegalesService.guardar_documento_expediente(request, admision)

            # Por defecto, recargar la misma página
            return redirect("admisiones_legales_ver", pk=admision.pk)
        except Exception:
            logger.exception(
                "Error en procesar_post_legales",
                extra={"admision_pk": admision.pk},
            )
            messages.error(request, "Error inesperado al procesar el POST de legales.")
            return redirect("admisiones_legales_ver", pk=admision.pk)

    @staticmethod
    def get_legales_context(admision):
        try:
            documentaciones = Documentacion.objects.filter(
                models.Q(convenios=admision.tipo_convenio)
            ).distinct()
            informe = LegalesService.get_informe_por_tipo_convenio(admision)
            archivos_subidos = ArchivoAdmision.objects.filter(admision=admision)
            informes_complementarios = InformeComplementario.objects.filter(
                admision=admision
            )
            historial = admision.historial.all().order_by("-fecha")

            archivos_dict = {}
            documentos_personalizados = []
            for archivo in archivos_subidos:
                if getattr(archivo, "documentacion_id", None):
                    archivos_dict[archivo.documentacion_id] = archivo
                else:
                    documentos_personalizados.append(
                        {
                            "id": archivo.id,
                            "nombre": archivo.nombre_personalizado
                            or "Documento adicional",
                            "archivo_url": (
                                archivo.archivo.url if archivo.archivo else None
                            ),
                        }
                    )

            documentos_info = [
                {
                    "id": doc.id,
                    "nombre": doc.nombre,
                    "archivo_url": (
                        archivos_dict[doc.id].archivo.url
                        if doc.id in archivos_dict
                        else None
                    ),
                }
                for doc in documentaciones
            ]

            documentos_info.extend(documentos_personalizados)

            reso_formulario = admision.admisiones_proyecto_disposicion.first()
            proyecto_formulario = admision.admisiones_proyecto_convenio.first()

            if reso_formulario:
                reso_form = ProyectoDisposicionForm(instance=reso_formulario)
                dispo_num_if_form = DisposicionNumIFFORM(instance=reso_formulario)
            else:
                reso_form = ProyectoDisposicionForm()
                dispo_num_if_form = DisposicionNumIFFORM()

            if proyecto_formulario:
                proyecto_form = ProyectoConvenioForm(instance=proyecto_formulario)
                convenio_num_if_form = ConvenioNumIFFORM(instance=proyecto_formulario)
            else:
                proyecto_form = ProyectoConvenioForm()
                convenio_num_if_form = ConvenioNumIFFORM()

            legales_num_if_form = LegalesNumIFForm(instance=admision)
            documentos_form = DocumentosExpedienteForm(initial={"admision": admision})

            documentos_expediente = DocumentosExpediente.objects.filter(
                admision=admision
            )

            tipos = ["Informe SGA", "Disposición", "Firma Convenio", "Numero CONV"]

            ultimos_valores = {}
            for tipo in tipos:
                ultimo_doc = (
                    documentos_expediente.filter(tipo=tipo).order_by("-creado").first()
                )
                ultimos_valores[tipo] = ultimo_doc.value if ultimo_doc else None

            return {
                "documentos": documentos_info,
                "informe": informe,
                "historial_cambios": historial,
                "pdf_url": (
                    getattr(admision, "informe_pdf", None).archivo.url
                    if getattr(admision, "informe_pdf", None)
                    and getattr(admision.informe_pdf, "archivo", None)
                    else None
                ),
                "formulario_reso": reso_formulario,
                "formulario_reso_completo": bool(reso_formulario),
                "formulario_proyecto": proyecto_formulario,
                "formulario_proyecto_completo": bool(proyecto_formulario),
                "reso_form": reso_form,
                "proyecto_form": proyecto_form,
                "form_legales_num_if": legales_num_if_form,
                "convenio_num_if": convenio_num_if_form,
                "dispo_num_if": dispo_num_if_form,
                "form_intervencion_juridicos": IntervencionJuridicosForm(
                    instance=admision
                ),
                "form_informe_sga": InformeSGAForm(instance=admision),
                "form_convenio": ConvenioForm(instance=admision),
                "form_disposicion": DisposicionForm(instance=admision),
                "form_reinicio_expediente": ReinicioExpedienteForm(instance=admision),
                "documentos_form": documentos_form,
                "value_informe_sga": ultimos_valores["Informe SGA"],
                "value_disposicion": ultimos_valores["Disposición"],
                "value_firma_convenio": ultimos_valores["Firma Convenio"],
                "value_numero_conv": ultimos_valores["Numero CONV"],
                "informes_complementarios": informes_complementarios,
            }
        except Exception:
            logger.exception(
                "Error en get_legales_context",
                extra={"admision_pk": admision.pk},
            )
            return {}

    @staticmethod
    def get_informe_por_tipo_convenio(admision):
        try:
            tipo = admision.tipo_informe
            if not tipo:
                return None
            return InformeTecnico.objects.filter(admision=admision, tipo=tipo).first()
        except Exception:
            logger.exception(
                "Error en get_informe_por_tipo_convenio",
                extra={"admision_pk": admision.pk},
            )
            return None
