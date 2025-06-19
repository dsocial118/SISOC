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
    InformeTecnico,
    InformeTecnicoPDF,
    DocumentosExpediente,
    Anexo,
    CampoASubsanar,
    ObservacionGeneralInforme,
    FormularioProyectoDisposicion,
    FormularioProyectoDeConvenio,
)
from admisiones.forms.admisiones_forms import (
    DocumentosExpedienteForm,
    InformeTecnicoJuridicoForm,
    InformeTecnicoBaseForm,
    CaratularForm,
    ProyectoConvenioForm,
    ProyectoDisposicionForm,
    LegalesNumIFForm,
    LegalesRectificarForm,
)
from comedores.models import Comedor
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from weasyprint import HTML
from django.templatetags.static import static
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

from acompanamientos.acompanamiento_service import AcompanamientoService


class AdmisionService:

    @staticmethod
    def get_comedores_with_admision(user):
        """Obtener comedores relacionados a un usuario.

        Args:
            user (User): Usuario para filtrar comedores.

        Returns:
            QuerySet: Comedores anotados con su admisión.
        """
        admision_subquery = Admision.objects.filter(comedor=OuterRef("pk"))

        if user.is_superuser:
            queryset = Comedor.objects.all()
        else:
            queryset = Comedor.objects.filter(
                Q(dupla__tecnico=user) | Q(dupla__abogado=user), dupla__estado="Activo"
            )

        return (
            queryset.annotate(
                admision_id=Subquery(admision_subquery.values("id")[:1]),
                estado_legales=Subquery(admision_subquery.values("estado_legales")[:1]),
            )
            .distinct()
            .order_by("-id")
        )

    @staticmethod
    def get_admision_create_context(pk):
        """Contexto inicial para la creación de una admisión.

        Args:
            pk (int): Clave primaria del comedor.

        Returns:
            dict: Datos necesarios para el formulario de admisión.
        """
        comedor = get_object_or_404(Comedor, pk=pk)
        convenios = TipoConvenio.objects.all()

        return {"comedor": comedor, "convenios": convenios, "es_crear": True}

    @staticmethod
    def create_admision(comedor_pk, tipo_convenio_id):
        """Crear una admisión asociada a un comedor y tipo de convenio.

        Args:
            comedor_pk (int): Identificador del comedor.
            tipo_convenio_id (int): Identificador del tipo de convenio.

        Returns:
            Admision: Instancia creada.
        """
        comedor = get_object_or_404(Comedor, pk=comedor_pk)
        tipo_convenio = get_object_or_404(TipoConvenio, pk=tipo_convenio_id)
        estado = 1

        return Admision.objects.create(
            comedor=comedor, tipo_convenio=tipo_convenio, estado_id=estado
        )

    @staticmethod
    def get_admision_update_context(admision):
        """Preparar el contexto necesario para actualizar una admisión.

        Args:
            admision (Admision): Instancia que será editada.

        Returns:
            dict: Datos para completar el formulario de actualización.
        """
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
        informe_tecnico = InformeTecnico.objects.filter(admision=admision).first()
        anexo = Anexo.objects.filter(admision=admision).first()
        pdf = InformeTecnicoPDF.objects.filter(admision=admision).first()

        return {
            "documentos": documentos_info,
            "comedor": comedor,
            "convenios": convenios,
            "caratular_form": caratular_form,
            "informe_tecnico": informe_tecnico,
            "anexo": anexo,
            "pdf": pdf,
        }

    @staticmethod
    def update_convenio(admision, nuevo_convenio_id):
        """Actualizar el tipo de convenio asociado a una admisión.

        Args:
            admision (Admision): Instancia a modificar.
            nuevo_convenio_id (int): Identificador del nuevo convenio.

        Returns:
            bool: ``True`` si se actualizó el convenio.
        """
        if not nuevo_convenio_id:
            return False

        nuevo_convenio = TipoConvenio.objects.get(pk=nuevo_convenio_id)
        admision.tipo_convenio = nuevo_convenio
        admision.save()

        ArchivoAdmision.objects.filter(admision=admision).delete()
        return True

    @staticmethod
    def handle_file_upload(admision_id, documentacion_id, archivo):
        """Guardar o reemplazar un archivo de documentación para una admisión.

        Args:
            admision_id (int): Identificador de la admisión.
            documentacion_id (int): Documento asociado.
            archivo (File): Archivo a guardar.

        Returns:
            tuple[ArchivoAdmision, bool]: Instancia y bandera de creación.
        """
        admision = get_object_or_404(Admision, pk=admision_id)
        documentacion = get_object_or_404(Documentacion, pk=documentacion_id)

        return ArchivoAdmision.objects.update_or_create(
            admision=admision,
            documentacion=documentacion,
            defaults={"archivo": archivo, "estado": "A Validar"},
        )

    @staticmethod
    def delete_admision_file(archivo):
        """Eliminar físicamente un archivo y su registro.

        Args:
            archivo (ArchivoAdmision): Archivo a eliminar.

        Returns:
            None
        """
        if archivo.archivo:
            file_path = os.path.join(settings.MEDIA_ROOT, str(archivo.archivo))
            if os.path.exists(file_path):
                os.remove(file_path)

        archivo.delete()

    @staticmethod
    def actualizar_estado_ajax(request):
        """Actualizar el estado de un archivo vía petición AJAX.

        Args:
            request (HttpRequest): Petición entrante con los datos necesarios.

        Returns:
            dict: Resultado de la operación.
        """
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
        """Cambiar el estado de un archivo y verificar la admisión.

        Args:
            archivo (ArchivoAdmision): Archivo a actualizar.
            nuevo_estado (str): Valor a asignar.

        Returns:
            bool: ``True`` si el cambio fue exitoso.
        """
        if not archivo:
            return False

        archivo.estado = nuevo_estado
        archivo.save()

        AdmisionService.verificar_estado_admision(archivo.admision)
        return True

    @staticmethod
    def verificar_estado_admision(admision):
        """Revisar si todos los archivos fueron aceptados y actualizar el estado.

        Args:
            admision (Admision): Instancia a validar.

        Returns:
            None
        """
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
        """Obtener el grupo principal asociado a un usuario de la dupla.

        Args:
            user (User): Usuario consultado.

        Returns:
            str: Nombre del grupo principal.
        """
        if user.groups.filter(name="Abogado Dupla").exists():
            return "Abogado Dupla"
        elif user.groups.filter(name="Tecnico Comedor").exists():
            return "Tecnico Comedor"
        else:
            return "Otro"

    @staticmethod
    def get_queryset_informe_por_tipo(tipo):
        """Devolver ``QuerySet`` de informes filtrados por tipo.

        Args:
            tipo (str): Tipo de informe a buscar.

        Returns:
            QuerySet: Conjunto de informes filtrado.
        """
        return InformeTecnico.objects.filter(tipo=tipo)

    @staticmethod
    def get_informe_por_tipo_y_pk(tipo, pk):
        """Obtener un informe por tipo y clave primaria.

        Args:
            tipo (str): Tipo de informe.
            pk (int): Identificador del informe.

        Returns:
            InformeTecnico: Instancia solicitada.
        """
        return get_object_or_404(InformeTecnico, tipo=tipo, pk=pk)

    @staticmethod
    def actualizar_estado_informe(informe, nuevo_estado, tipo=None):
        """Modificar el estado del informe y generar el PDF si corresponde.

        Args:
            informe (InformeTecnico): Informe a actualizar.
            nuevo_estado (str): Nuevo estado a aplicar.
            tipo (str | None): Tipo de informe para generar PDF.

        Returns:
            None
        """
        informe.estado = nuevo_estado
        informe.save()

        if nuevo_estado == "Validado":
            AdmisionService.generar_y_guardar_pdf(informe, tipo)

    @staticmethod
    def generar_y_guardar_pdf(informe, tipo):
        """Crear un archivo PDF a partir del informe técnico.

        Args:
            informe (InformeTecnico): Informe fuente.
            tipo (str): Tipo de informe (juridico/base).

        Returns:
            None
        """
        campos = [
            (field.verbose_name, field.value_from_object(informe))
            for field in informe._meta.fields
            if field.name not in ["id", "admision", "estado"]
        ]

        html_string = render_to_string(
            "pdf_informe_tecnico.html",
            {
                "informe": informe,
                "campos": campos,
            },
        )

        pdf_file = HTML(string=html_string).write_pdf()

        nombre_archivo = f"{tipo}_informe_{informe.id}.pdf"
        pdf_content = ContentFile(pdf_file, name=nombre_archivo)

        InformeTecnicoPDF.objects.create(
            admision=informe.admision,
            tipo=tipo,
            informe_id=informe.id,
            archivo=pdf_content,
        )

    @staticmethod
    def get_campos_visibles_informe(informe):
        """Listar pares de etiquetas y valores visibles para un informe.

        Args:
            informe (InformeTecnico): Informe a procesar.

        Returns:
            list[tuple[str, Any]]: Pares de etiqueta y valor visibles.
        """
        campos_excluidos_comunes = ["id", "admision", "estado", "tipo"]

        if informe.tipo == "juridico":
            campos_excluidos_especificos = [
                "declaracion_jurada_recepcion_subsidios",
                "constancia_inexistencia_percepcion_otros_subsidios",
                "organizacion_avalista_1",
                "organizacion_avalista_2",
                "material_difusion_vinculado",
            ]
        elif informe.tipo == "base":
            campos_excluidos_especificos = [
                "validacion_registro_nacional",
                "IF_relevamiento_territorial",
            ]
        else:
            campos_excluidos_especificos = []

        campos_excluidos = campos_excluidos_comunes + campos_excluidos_especificos

        return [
            (field.verbose_name, getattr(informe, field.name))
            for field in informe._meta.fields
            if field.name not in campos_excluidos
        ]

    @staticmethod
    def get_admision(admision_id):
        """Obtener una admisión existente o lanzar ``404``.

        Args:
            admision_id (int): Identificador de la admisión.

        Returns:
            Admision: Instancia solicitada.
        """
        return get_object_or_404(Admision, pk=admision_id)

    @staticmethod
    def get_form_class_por_tipo(tipo):
        """Devolver la clase de formulario correspondiente según el tipo.

        Args:
            tipo (str): Tipo de informe.

        Returns:
            type[forms.Form]: Clase de formulario adecuada.
        """
        return (
            InformeTecnicoJuridicoForm if tipo == "juridico" else InformeTecnicoBaseForm
        )

    @staticmethod
    def preparar_informe_para_creacion(instance, admision_id):
        """Configurar los valores iniciales de un informe recién creado.

        Args:
            instance (InformeTecnico): Informe a preparar.
            admision_id (int): Identificador de la admisión vinculada.

        Returns:
            None
        """
        instance.admision_id = admision_id
        instance.estado = "Para revision"

    @staticmethod
    def verificar_estado_para_revision(informe):
        """Resetear observaciones y dejar el informe listo para revisión.

        Args:
            informe (InformeTecnico): Informe a modificar.

        Returns:
            None
        """
        if informe.estado != "Validado":
            CampoASubsanar.objects.filter(informe=informe).delete()
            ObservacionGeneralInforme.objects.filter(informe=informe).delete()
            informe.estado = "Para revision"

    @staticmethod
    def marcar_como_enviado_a_legales(admision, usuario=None):
        """Marcar la admisión como enviada a legales.

        Args:
            admision (Admision): Instancia a actualizar.
            usuario (User | None): Usuario que ejecuta la acción.

        Returns:
            bool: ``True`` si se modificó el estado.
        """
        if not admision.enviado_legales:
            admision.enviado_legales = True
            admision.save()
            return True
        return False

    @staticmethod
    def marcar_como_enviado_a_acompaniamiento(admision, usuario=None):
        """Marcar la admisión como enviada a acompañamiento.

        Args:
            admision (Admision): Instancia a actualizar.
            usuario (User | None): Usuario que ejecuta la acción.

        Returns:
            bool: ``True`` si se modificó el estado.
        """
        if not admision.enviado_acompaniamiento:
            admision.enviado_acompaniamiento = True
            admision.save()
            return True
        return False

    @staticmethod
    def marcar_como_documentacion_rectificada(admision, usuario=None):
        """Indicar que la documentación fue rectificada y actualizar estados.

        Args:
            admision (Admision): Instancia a modificar.
            usuario (User | None): Usuario que realiza el cambio.

        Returns:
            bool: ``True`` si hubo modificaciones.
        """
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
        """Armar el contexto utilizado en la vista de legales.

        Args:
            admision (Admision): Instancia sobre la que se trabaja.

        Returns:
            dict: Datos a renderizar en la vista.
        """
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

        reso_formulario = admision.proyecto_disposicion.first()
        proyecto_formulario = admision.proyecto_convenio.first()
        reso_form = ProyectoDisposicionForm(instance=admision)
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
        """Obtener el informe correspondiente al tipo de convenio.

        Args:
            admision (Admision): Instancia de referencia.

        Returns:
            InformeTecnico | None: Informe encontrado o ``None``.
        """
        tipo = admision.tipo_informe
        if not tipo:
            return None
        return InformeTecnico.objects.filter(admision=admision, tipo=tipo).first()

    @staticmethod
    def enviar_a_rectificar(request, admision):
        """Enviar la admisión a rectificación registrando observaciones.

        Args:
            request (HttpRequest): Petición con los datos ingresados.
            admision (Admision): Instancia que se actualizará.

        Returns:
            HttpResponseRedirect: Redirección a la misma página.
        """
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
        """Guardar el número de IF provisto por legales.

        Args:
            request (HttpRequest): Petición con el número ingresado.
            admision (Admision): Instancia a modificar.

        Returns:
            HttpResponseRedirect: Redirección a la página actual.
        """
        form = LegalesNumIFForm(request.POST, instance=admision)
        if form.is_valid():
            form.save()
            messages.success(request, "Número de IF guardado correctamente.")
        else:
            messages.error(request, "Error al guardar el número de IF.")
        return redirect(request.path_info)

    @staticmethod
    def validar_juridicos(request, admision):
        """Cambiar el estado a 'Pendiente de Validación' si se cumplen requisitos.

        Args:
            request (HttpRequest): Petición de validación.
            admision (Admision): Instancia sobre la que se opera.

        Returns:
            HttpResponseRedirect: Redirección a la página actual.
        """
        reso_completo = FormularioProyectoDisposicion.objects.filter(
            admision=admision
        ).exists()
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
        """Guardar el formulario de disposición y generar su PDF.

        Args:
            request (HttpRequest): Datos del formulario enviado.
            admision (Admision): Instancia relacionada.

        Returns:
            HttpResponseRedirect: Redirección al mismo URL.
        """
        formulario_existente = FormularioProyectoDisposicion.objects.filter(
            admision=admision
        ).first()
        form = ProyectoDisposicionForm(request.POST, instance=formulario_existente)

        if form.is_valid():
            nuevo_formulario = form.save(commit=False)
            nuevo_formulario.admision = admision
            nuevo_formulario.creado_por = request.user
            nuevo_formulario.save()

            if nuevo_formulario.tipo == "incorporacion":
                template_name = "pdf_dispo_incorporacion.html"
            else:
                template_name = "pdf_dispo_renovacion.html"

            context = {
                "admision": admision,
                "formulario": nuevo_formulario,
            }
            html_string = render_to_string(template_name, context)

            pdf_filename = f"disposicion_{admision.id}_{nuevo_formulario.id}.pdf"
            pdf_path = os.path.join(
                settings.MEDIA_ROOT, "formularios_disposicion", pdf_filename
            )

            os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

            HTML(string=html_string).write_pdf(pdf_path)

            nuevo_formulario.archivo.name = f"formularios_disposicion/{pdf_filename}"
            nuevo_formulario.save()

            messages.success(
                request, "Formulario guardado y PDF generado correctamente."
            )
        else:
            messages.error(request, "Error al guardar el formulario RESO.")

        return redirect(request.path_info)

    @staticmethod
    def guardar_formulario_proyecto_convenio(request, admision):
        """Persistir el formulario de convenio y generar el PDF asociado.

        Args:
            request (HttpRequest): Petición entrante.
            admision (Admision): Instancia relacionada.

        Returns:
            HttpResponseRedirect: Redirección al mismo URL.
        """
        formulario_existente = FormularioProyectoDeConvenio.objects.filter(
            admision=admision
        ).first()
        form = ProyectoConvenioForm(request.POST, instance=formulario_existente)

        if form.is_valid():
            nuevo_formulario = form.save(commit=False)
            nuevo_formulario.admision = admision
            nuevo_formulario.creado_por = request.user
            nuevo_formulario.save()

            context = {
                "admision": admision,
                "formulario": nuevo_formulario,
            }
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
                request,
                "PDF de Formulario Proyecto de Convenio generado correctamente.",
            )
        else:
            messages.error(
                request, "Error al guardar el formulario Proyecto de Convenio."
            )

        return redirect(request.path_info)

    @staticmethod
    def guardar_documento_expediente(request, admision):
        """Registrar un nuevo documento de expediente y actualizar el estado.

        Args:
            request (HttpRequest): Datos y archivos enviados.
            admision (Admision): Instancia sobre la que se guarda.

        Returns:
            HttpResponseRedirect: Redirección a la página actual.
        """
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
        """Iniciar el acompañamiento importando datos desde la admisión.

        Args:
            admision_id (int): Identificador de la admisión.

        Returns:
            Admision: Instancia actualizada.
        """
        admision = get_object_or_404(Admision, pk=admision_id)
        estado_admitido = EstadoAdmision.objects.get(
            nombre="Admitido - pendiente ejecución"
        )
        admision.estado = estado_admitido
        admision.save()

        AcompanamientoService.importar_datos_desde_admision(admision.comedor)

        return admision
