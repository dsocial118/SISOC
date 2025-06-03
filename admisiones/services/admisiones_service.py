import os
from django.conf import settings
from django.db import models
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.db.models import OuterRef, Subquery
from admisiones.models.admisiones import (
    Admision,
    EstadoAdmision,
    TipoConvenio,
    Documentacion,
    ArchivoAdmision,
    InformeTecnicoBase,
    InformeTecnicoJuridico,
    InformeTecnicoPDF,
    DocumentosExpediente,
)
from admisiones.forms.admisiones_forms import (
    DocumentosExpedienteForm,
    InformeTecnicoJuridicoForm,
    InformeTecnicoBaseForm,
    CaratularForm,
    ProyectoConvenioForm,
    ResoForm,
    LegalesNumIFForm,
    FormularioRESO,
    FormularioProyectoDeConvenio,
    LegalesRectificarForm,
)
from comedores.models.comedor import Comedor
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from io import BytesIO
from django.forms.models import model_to_dict
from xhtml2pdf import pisa
import logging

logger = logging.getLogger(__name__)

from acompanamientos.acompanamiento_service import AcompanamientoService


class AdmisionService:

    @staticmethod
    def get_comedores_with_admision(user):
        admision_subquery = Admision.objects.filter(comedor=OuterRef("pk")).values(
            "id"
        )[:1]

        return (
            Comedor.objects.filter(
                Q(dupla__tecnico=user) | Q(dupla__abogado=user), dupla__estado="Activo"
            )
            .annotate(
                admision_id=Subquery(admision_subquery.values("id")[:1]),
                estado_legales=Subquery(admision_subquery.values("estado_legales")[:1]),
            )
            .distinct()
            .order_by("-id")
        )

    @staticmethod
    def get_admision_create_context(pk):
        comedor = get_object_or_404(Comedor, pk=pk)
        convenios = TipoConvenio.objects.all()

        return {"comedor": comedor, "convenios": convenios, "es_crear": True}

    @staticmethod
    def create_admision(comedor_pk, tipo_convenio_id):
        comedor = get_object_or_404(Comedor, pk=comedor_pk)
        tipo_convenio = get_object_or_404(TipoConvenio, pk=tipo_convenio_id)
        estado = 1

        return Admision.objects.create(
            comedor=comedor, tipo_convenio=tipo_convenio, estado_id=estado
        )

    @staticmethod
    def get_admision_update_context(admision):
        documentaciones = Documentacion.objects.filter(
            models.Q(convenios=admision.tipo_convenio)
        ).distinct()

        archivos_subidos = ArchivoAdmision.objects.filter(admision=admision)

        archivos_dict = {
            archivo.documentacion.id: archivo for archivo in archivos_subidos
        }

        documentos_info = [
            {
                "id": doc.id,
                "nombre": doc.nombre,
                "estado": (
                    archivos_dict.get(doc.id).estado
                    if doc.id in archivos_dict
                    else "Pendiente"
                ),
                "archivo_url": (
                    archivos_dict[doc.id].archivo.url
                    if doc.id in archivos_dict
                    else None
                ),
            }
            for doc in documentaciones
        ]

        comedor = Comedor.objects.get(pk=admision.comedor_id)
        convenios = TipoConvenio.objects.all()
        caratular_form = CaratularForm(instance=admision)
        informe_base = InformeTecnicoBase.objects.filter(admision=admision).first()
        informe_juridico = InformeTecnicoJuridico.objects.filter(
            admision=admision
        ).first()
        return {
            "documentos": documentos_info,
            "comedor": comedor,
            "convenios": convenios,
            "caratular_form": caratular_form,
            "informe_base": informe_base,
            "informe_juridico": informe_juridico,
        }

    @staticmethod
    def update_convenio(admision, nuevo_convenio_id):
        if not nuevo_convenio_id:
            return False

        nuevo_convenio = TipoConvenio.objects.get(pk=nuevo_convenio_id)
        admision.tipo_convenio = nuevo_convenio
        admision.save()

        ArchivoAdmision.objects.filter(admision=admision).delete()
        return True

    @staticmethod
    def handle_file_upload(admision_id, documentacion_id, archivo):
        admision = get_object_or_404(Admision, pk=admision_id)
        documentacion = get_object_or_404(Documentacion, pk=documentacion_id)

        return ArchivoAdmision.objects.update_or_create(
            admision=admision,
            documentacion=documentacion,
            defaults={"archivo": archivo, "estado": "A Validar"},
        )

    @staticmethod
    def delete_admision_file(archivo):
        if archivo.archivo:
            file_path = os.path.join(settings.MEDIA_ROOT, str(archivo.archivo))
            if os.path.exists(file_path):
                os.remove(file_path)

        archivo.delete()

    @staticmethod
    def actualizar_estado_ajax(request):
        estado = request.POST.get("estado")
        documento_id = request.POST.get("documento_id")
        admision_id = request.POST.get("admision_id")

        if not all([estado, documento_id, admision_id]):
            return {"success": False, "error": "Datos incompletos."}

        try:
            archivo = get_object_or_404(
                ArchivoAdmision, admision_id=admision_id, documentacion_id=documento_id
            )

            exito = AdmisionService.update_estado_archivo(archivo, estado)

            if not exito:
                return {"success": False, "error": "No se pudo actualizar el estado."}

            grupo_usuario = AdmisionService.get_dupla_grupo_por_usuario(request.user)

            return {
                "success": True,
                "nuevo_estado": archivo.estado,
                "grupo_usuario": grupo_usuario,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def update_estado_archivo(archivo, nuevo_estado):
        if not archivo:
            return False

        archivo.estado = nuevo_estado
        archivo.save()

        AdmisionService.verificar_estado_admision(archivo.admision)
        return True

    @staticmethod
    def verificar_estado_admision(admision):
        archivos = ArchivoAdmision.objects.filter(admision=admision).only("estado")

        if admision.estado_id != 3:
            if archivos.exists() and all(
                archivo.estado == "Aceptado" for archivo in archivos
            ):
                if admision.estado_id != 2:
                    admision.estado_id = 2
                    admision.save()

    @staticmethod
    def get_dupla_grupo_por_usuario(user):
        if user.groups.filter(name="Abogado Dupla").exists():
            return "Abogado Dupla"
        elif user.groups.filter(name="Tecnico Comedor").exists():
            return "Tecnico Comedor"
        else:
            return "Otro"

    @staticmethod
    def get_queryset_informe_por_tipo(tipo):
        return (
            InformeTecnicoJuridico.objects.all()
            if tipo == "juridico"
            else InformeTecnicoBase.objects.all()
        )

    @staticmethod
    def get_informe_por_tipo_y_pk(tipo, pk):
        modelo = InformeTecnicoJuridico if tipo == "juridico" else InformeTecnicoBase
        return get_object_or_404(modelo, pk=pk)

    @staticmethod
    def actualizar_estado_informe(informe, nuevo_estado, tipo):
        informe.estado = nuevo_estado
        informe.save()
        if nuevo_estado == "Validado":
            AdmisionService.generar_y_guardar_pdf(informe, tipo)

    @staticmethod
    def generar_y_guardar_pdf(informe, tipo):
        campos = [
            (field.verbose_name, field.value_from_object(informe))
            for field in informe._meta.fields
            if field.name not in ["id", "admision", "estado"]
        ]

        html = render_to_string(
            "pdf_template.html",
            {
                "informe": informe,
                "campos": campos,
            },
        )

        result = BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=result)
        if pisa_status.err:
            logger.error("Error al generar el PDF con pisa: %s", pisa_status.err)
            return

        nombre_archivo = f"{tipo}_informe_{informe.id}.pdf"
        pdf_file = ContentFile(result.getvalue(), name=nombre_archivo)

        InformeTecnicoPDF.objects.create(
            admision=informe.admision,
            tipo=tipo,
            informe_id=informe.id,
            archivo=pdf_file,
        )

    @staticmethod
    def get_campos_visibles_informe(informe):
        return [
            (field.verbose_name, getattr(informe, field.name))
            for field in informe._meta.get_fields()
            if field.name not in ["id", "admision", "estado"]
        ]

    @staticmethod
    def get_admision(admision_id):
        return get_object_or_404(Admision, pk=admision_id)

    @staticmethod
    def get_form_class_por_tipo(tipo):
        return (
            InformeTecnicoJuridicoForm if tipo == "juridico" else InformeTecnicoBaseForm
        )

    @staticmethod
    def preparar_informe_para_creacion(instance, admision_id):
        instance.admision_id = admision_id
        instance.estado = "Para revision"

    @staticmethod
    def verificar_estado_para_revision(informe):
        if informe.estado != "Validado":
            informe.estado = "Para revision"

    @staticmethod
    def marcar_como_enviado_a_legales(admision, usuario=None):
        if not admision.enviado_legales:
            admision.enviado_legales = True
            admision.save()
            return True
        return False

    @staticmethod
    def marcar_como_documentacion_rectificada(admision, usuario=None):
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

    @staticmethod
    def get_legales_context(admision):
        documentaciones = Documentacion.objects.filter(
            models.Q(convenios=admision.tipo_convenio)
        ).distinct()
        informe = AdmisionService.get_informe_por_tipo_convenio(admision)
        archivos_subidos = ArchivoAdmision.objects.filter(admision=admision)
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

        reso_formulario = admision.formularios_reso.first()
        proyecto_formulario = admision.formularios_proyecto_convenio.first()
        reso_form = ResoForm(instance=admision)
        proyecto_form = ProyectoConvenioForm(instance=admision)
        legales_num_if_form = LegalesNumIFForm(instance=admision)
        documentos_form = DocumentosExpedienteForm(initial={"admision": admision})

        documentos_expediente = DocumentosExpediente.objects.filter(admision=admision)

        tipos = ["Informe SGA", "Resolución", "Firma Convenio", "Numero CONV"]

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
            "value_resolucion": ultimos_valores["Resolución"],
            "value_firma_convenio": ultimos_valores["Firma Convenio"],
            "value_numero_conv": ultimos_valores["Numero CONV"],
        }

    @staticmethod
    def get_informe_por_tipo_convenio(admision):
        if admision.tipo_convenio_id == 1:
            return InformeTecnicoBase.objects.filter(admision=admision).first()
        elif admision.tipo_convenio_id in [2, 3]:
            return InformeTecnicoJuridico.objects.filter(admision=admision).first()
        return None

    @staticmethod
    def enviar_a_rectificar(request, admision):
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
        return redirect(request.path_info)

    @staticmethod
    def guardar_legales_num_if(request, admision):
        form = LegalesNumIFForm(request.POST, instance=admision)
        if form.is_valid():
            form.save()
            messages.success(request, "Número de IF guardado correctamente.")
        else:
            messages.error(request, "Error al guardar el número de IF.")
        return redirect(request.path_info)

    @staticmethod
    def validar_juridicos(request, admision):
        reso_completo = FormularioRESO.objects.filter(admision=admision).exists()
        proyecto_completo = FormularioProyectoDeConvenio.objects.filter(
            admision=admision
        ).exists()

        condiciones_validas = (
            reso_completo
            and proyecto_completo
            and (admision.observaciones is None or admision.observaciones.strip() == "")
            and admision.estado_legales != "A Rectificar"
            and admision.legales_num_if not in [None, ""]
        )

        if condiciones_validas:
            admision.estado_legales = "Pendiente de Validacion"
            admision.save()
            messages.success(request, "Estado cambiado a 'Pendiente de Validacion'.")
        else:
            messages.error(
                request,
                "No se puede validar: asegúrese de que completar ambos formularios y agregar el Número IF.",
            )

        return redirect(request.path_info)

    @staticmethod
    def guardar_formulario_reso(request, admision):
        formulario_existente = FormularioRESO.objects.filter(admision=admision).first()
        form = ResoForm(request.POST, instance=formulario_existente)

        if form.is_valid():
            nuevo_formulario = form.save(commit=False)
            nuevo_formulario.admision = admision
            nuevo_formulario.creado_por = request.user
            nuevo_formulario.save()
            messages.success(request, "Formulario RESO guardado correctamente.")
        else:
            messages.error(request, "Error al guardar el formulario RESO.")

        return redirect(request.path_info)

    @staticmethod
    def guardar_formulario_proyecto_convenio(request, admision):
        formulario_existente = FormularioProyectoDeConvenio.objects.filter(
            admision=admision
        ).first()
        form = ProyectoConvenioForm(request.POST, instance=formulario_existente)

        if form.is_valid():
            nuevo_formulario = form.save(commit=False)
            nuevo_formulario.admision = admision
            nuevo_formulario.creado_por = request.user
            nuevo_formulario.save()
            messages.success(
                request, "Formulario Proyecto de Convenio guardado correctamente."
            )
        else:
            messages.error(
                request, "Error al guardar el formulario Proyecto de Convenio."
            )

        return redirect(request.path_info)

    @staticmethod
    def guardar_documento_expediente(request, admision):
        form = DocumentosExpedienteForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.admision = admision
            documento.save()

            cambio_estado = {
                "Informe SGA": "Informe SGA Generado",
                "Resolución": "Resolución Generada",
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
            logger.error("Error al guardar documento de expediente: %s", form.errors)

        return redirect(request.path_info)

    @staticmethod
    def comenzar_acompanamiento(admision_id):
        admision = get_object_or_404(Admision, pk=admision_id)
        estado_admitido = EstadoAdmision.objects.get(
            nombre="Admitido - pendiente ejecución"
        )
        admision.estado = estado_admitido
        admision.save()

        # Importar datos a la app de Acompañamiento
        AcompanamientoService.importar_datos_desde_admision(admision.comedor)

        return admision
