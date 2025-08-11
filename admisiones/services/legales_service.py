from django.utils.http import url_has_allowed_host_and_scheme
from django.shortcuts import redirect
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.db import models
from django.template.loader import render_to_string
from weasyprint import HTML
import os
from django.conf import settings
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)

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
        except Exception as e:
            logger.error(
                "Ocurrió un error inesperado en enviar_a_rectificar", exc_info=True
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
        except Exception as e:
            logger.error(
                "Ocurrió un error inesperado en guardar_legales_num_if", exc_info=True
            )
            messages.error(request, "Error inesperado al guardar el número de IF.")
            if url_has_allowed_host_and_scheme(
                request.path_info, allowed_hosts={request.get_host()}
            ):
                return redirect(request.path_info)
            else:
                return redirect("admisiones_legales_ver", pk=admision.pk)

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
        except Exception as e:
            logger.error(
                "Ocurrió un error inesperado en validar_juridicos", exc_info=True
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

            if form.is_valid():
                nuevo_formulario = form.save(commit=False)
                nuevo_formulario.admision = admision
                nuevo_formulario.creado_por = request.user
                nuevo_formulario.save()

                informe = (
                    InformeTecnico.objects.filter(admision=admision)
                    .order_by("-id")
                    .first()
                )

                template_name = (
                    "pdf_dispo_incorporacion.html"
                    if nuevo_formulario.tipo == "incorporacion"
                    else "pdf_dispo_renovacion.html"
                )

                context = {
                    "admision": admision,
                    "formulario": nuevo_formulario,
                    "informe": informe,
                }

                html_string = render_to_string(template_name, context)

                pdf_filename = f"disposicion_{admision.id}_{nuevo_formulario.id}.pdf"
                pdf_path = os.path.join(
                    settings.MEDIA_ROOT, "formularios_disposicion", pdf_filename
                )

                os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
                HTML(string=html_string).write_pdf(pdf_path)

                nuevo_formulario.archivo.name = (
                    f"formularios_disposicion/{pdf_filename}"
                )
                nuevo_formulario.save()

                messages.success(
                    request, "Formulario guardado y PDF generado correctamente."
                )
            else:
                messages.error(request, "Error al guardar el formulario RESO.")

            return redirect("admisiones_legales_ver", pk=admision.pk)
        except Exception as e:
            logger.error(
                "Ocurrió un error inesperado en guardar_formulario_reso", exc_info=True
            )
            messages.error(request, "Error inesperado al guardar el formulario RESO.")
            return redirect("admisiones_legales_ver", pk=admision.pk)

    @staticmethod
    def guardar_formulario_proyecto_convenio(request, admision):
        try:
            formulario_existente = FormularioProyectoDeConvenio.objects.filter(
                admision=admision
            ).first()
            form = ProyectoConvenioForm(request.POST, instance=formulario_existente)

            if form.is_valid():
                nuevo_formulario = form.save(commit=False)
                nuevo_formulario.admision = admision
                nuevo_formulario.creado_por = request.user
                nuevo_formulario.save()

                context = {"admision": admision, "formulario": nuevo_formulario}
                html_string = render_to_string("pdf_convenio.html", context)

                pdf_filename = f"convenio_{admision.id}_{nuevo_formulario.id}.pdf"
                pdf_path = os.path.join(
                    settings.MEDIA_ROOT, "formularios_convenio", pdf_filename
                )

                os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
                HTML(string=html_string).write_pdf(pdf_path)

                nuevo_formulario.archivo.name = f"formularios_convenio/{pdf_filename}"
                nuevo_formulario.save()

                messages.success(
                    request, "PDF de Proyecto de Convenio generado correctamente."
                )
            else:
                messages.error(
                    request, "Error al guardar el formulario Proyecto de Convenio."
                )

            return redirect(request.path_info)
        except Exception as e:
            logger.error(
                "Ocurrió un error inesperado en guardar_formulario_proyecto_convenio",
                exc_info=True,
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
        except Exception as e:
            logger.error(
                "Ocurrió un error inesperado en guardar_documento_expediente",
                exc_info=True,
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
        except Exception as e:
            logger.error(
                "Ocurrió un error inesperado en get_admisiones_legales_filtradas",
                exc_info=True,
            )
            return Admision.objects.none()

    @staticmethod
    def procesar_post_legales(request, admision):
        try:
            if "btnLegalesNumIF" in request.POST:
                return LegalesService.guardar_legales_num_if(request, admision)

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
        except Exception as e:
            logger.error(
                "Ocurrió un error inesperado en procesar_post_legales", exc_info=True
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

            archivos_dict = {
                archivo.documentacion.id: archivo for archivo in archivos_subidos
            }

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

            reso_formulario = admision.proyecto_disposicion.first()
            proyecto_formulario = admision.proyecto_convenio.first()
            reso_form = ProyectoDisposicionForm(instance=admision)
            proyecto_form = ProyectoConvenioForm(instance=admision)
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
                "documentos_form": documentos_form,
                "value_informe_sga": ultimos_valores["Informe SGA"],
                "value_disposicion": ultimos_valores["Disposición"],
                "value_firma_convenio": ultimos_valores["Firma Convenio"],
                "value_numero_conv": ultimos_valores["Numero CONV"],
                "informes_complementarios": informes_complementarios,
            }
        except Exception as e:
            logger.error(
                "Ocurrió un error inesperado en get_legales_context", exc_info=True
            )
            return {}

    @staticmethod
    def get_informe_por_tipo_convenio(admision):
        try:
            tipo = admision.tipo_informe
            if not tipo:
                return None
            return InformeTecnico.objects.filter(admision=admision, tipo=tipo).first()
        except Exception as e:
            logger.error(
                "Ocurrió un error inesperado en get_informe_por_tipo_convenio",
                exc_info=True,
            )
            return None
