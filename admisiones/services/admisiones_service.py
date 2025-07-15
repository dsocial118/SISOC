import os
from django.conf import settings
from django.db import models
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
    Anexo,
    CampoASubsanar,
    ObservacionGeneralInforme,
    InformeComplementario,
)
from admisiones.forms.admisiones_forms import (
    CaratularForm,
)
from comedores.models import Comedor
from django.db.models import Q
from django.shortcuts import get_object_or_404
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
    def get_comedores_filtrados(user, query=""):
        """
        Devuelve los comedores filtrados por búsqueda si corresponde.

        Args:
            user (User): Usuario actual.
            query (str): Texto de búsqueda.

        Returns:
            QuerySet: Comedores filtrados.
        """
        comedores = AdmisionService.get_comedores_with_admision(user)

        if query:
            query = query.strip().lower()
            comedores = comedores.filter(
                Q(nombre__icontains=query)
                | Q(provincia__nombre__icontains=query)
                | Q(tipocomedor__nombre__icontains=query)
                | Q(calle__icontains=query)
                | Q(numero__icontains=query)
                | Q(referente__nombre__icontains=query)
                | Q(referente__apellido__icontains=query)
                | Q(referente__celular__icontains=query)
            )

        return comedores

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
        informes_complementarios = InformeComplementario.objects.filter(
            admision=admision
        )
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
            "informes_complementarios": informes_complementarios,
        }

    @staticmethod
    def procesar_post_update(request, admision):
        """
        Procesa los posibles botones del formulario de edición.

        Args:
            request (HttpRequest)
            admision (Admision)

        Returns:
            (HttpResponseRedirect, str): La redirección y mensaje opcional.
        """
        if "mandarLegales" in request.POST:
            if AdmisionService.marcar_como_enviado_a_legales(admision, request.user):
                return True, "La admisión fue enviada a legales correctamente."
            return False, "La admisión ya estaba marcada como enviada a legales."

        if "btnDisponibilizarAcomp" in request.POST:
            if AdmisionService.marcar_como_enviado_a_acompaniamiento(
                admision, request.user
            ):
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
                return True, "Caratulación del expediente guardado correctamente."
            return False, "Error al guardar la caratulación."

        if "tipo_convenio" in request.POST:
            if AdmisionService.update_convenio(
                admision, request.POST.get("tipo_convenio")
            ):
                return True, "Tipo de convenio actualizado correctamente."

        return None, None

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
    def get_admision(admision_id):
        """Obtener una admisión existente o lanzar ``404``.

        Args:
            admision_id (int): Identificador de la admisión.

        Returns:
            Admision: Instancia solicitada.
        """
        return get_object_or_404(Admision, pk=admision_id)

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

    @staticmethod
    def get_admision_context(admision_id):
        """
        Devuelve el contexto para renderizar un formulario vinculado a una admisión.
        """
        admision = get_object_or_404(Admision, id=admision_id)
        return {"admision": admision}

    @staticmethod
    def get_admision_instance(admision_id):
        """
        Devuelve la instancia de admisión o lanza 404.
        """
        return get_object_or_404(Admision, id=admision_id)
