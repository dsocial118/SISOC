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
        try:
            admision_subquery = Admision.objects.filter(comedor=OuterRef("pk"))

            if user.is_superuser:
                queryset = Comedor.objects.all()
            else:
                queryset = Comedor.objects.filter(
                    Q(dupla__tecnico=user) | Q(dupla__abogado=user),
                    dupla__estado="Activo",
                )

            return (
                queryset.annotate(
                    admision_id=Subquery(admision_subquery.values("id")[:1]),
                    estado_legales=Subquery(
                        admision_subquery.values("estado_legales")[:1]
                    ),
                )
                .distinct()
                .order_by("-id")
            )
        except Exception as e:
            logger.error(
                "Error en get_comedores_with_admision",
                exc_info=True,
            )
            return Comedor.objects.none()

    @staticmethod
    def get_comedores_filtrados(user, query=""):
        try:
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
        except Exception as e:
            logger.error("Error en get_comedores_filtrados", exc_info=True)
            return Comedor.objects.none()

    @staticmethod
    def get_admision_create_context(pk):
        try:
            comedor = get_object_or_404(Comedor, pk=pk)
            convenios = TipoConvenio.objects.all()
            return {"comedor": comedor, "convenios": convenios, "es_crear": True}
        except Exception as e:
            logger.error(
                "Error en get_admision_create_context",
                exc_info=True,
            )
            return {}

    @staticmethod
    def create_admision(comedor_pk, tipo_convenio_id):
        try:
            comedor = get_object_or_404(Comedor, pk=comedor_pk)
            tipo_convenio = get_object_or_404(TipoConvenio, pk=tipo_convenio_id)
            estado = 1

            return Admision.objects.create(
                comedor=comedor, tipo_convenio=tipo_convenio, estado_id=estado
            )
        except Exception as e:
            logger.error("Error en create_admision", exc_info=True)
            return None

    @staticmethod
    def get_admision_update_context(admision):
        try:
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
        except Exception as e:
            logger.error(
                "Error en get_admision_update_context",
                exc_info=True,
            )
            return {}

    @staticmethod
    def procesar_post_update(request, admision):
        try:
            if "mandarLegales" in request.POST:
                if AdmisionService.marcar_como_enviado_a_legales(
                    admision, request.user
                ):
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
        except Exception as e:
            logger.error("Error en procesar_post_update", exc_info=True)
            return None, "Error inesperado."

    @staticmethod
    def update_convenio(admision, nuevo_convenio_id):
        try:
            if not nuevo_convenio_id:
                return False

            nuevo_convenio = TipoConvenio.objects.get(pk=nuevo_convenio_id)
            admision.tipo_convenio = nuevo_convenio
            admision.save()

            ArchivoAdmision.objects.filter(admision=admision).delete()
            return True
        except Exception as e:
            logger.error("Error en update_convenio", exc_info=True)
            return False

    @staticmethod
    def handle_file_upload(admision_id, documentacion_id, archivo):
        try:
            admision = get_object_or_404(Admision, pk=admision_id)
            documentacion = get_object_or_404(Documentacion, pk=documentacion_id)

            return ArchivoAdmision.objects.update_or_create(
                admision=admision,
                documentacion=documentacion,
                defaults={"archivo": archivo, "estado": "A Validar"},
            )
        except Exception as e:
            logger.error("Error en handle_file_upload", exc_info=True)
            return None, False

    @staticmethod
    def delete_admision_file(archivo):
        try:
            if archivo.archivo:
                file_path = os.path.join(settings.MEDIA_ROOT, str(archivo.archivo))
                if os.path.exists(file_path):
                    os.remove(file_path)

            archivo.delete()
        except Exception as e:
            logger.error("Error en delete_admision_file", exc_info=True)

    @staticmethod
    def actualizar_estado_ajax(request):
        try:
            estado = request.POST.get("estado")
            documento_id = request.POST.get("documento_id")
            admision_id = request.POST.get("admision_id")

            if not all([estado, documento_id, admision_id]):
                return {"success": False, "error": "Datos incompletos."}

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
            logger.error("Error en actualizar_estado_ajax", exc_info=True)
            return {"success": False, "error": str(e)}

    @staticmethod
    def update_estado_archivo(archivo, nuevo_estado):
        try:
            if not archivo:
                return False

            archivo.estado = nuevo_estado
            archivo.save()

            AdmisionService.verificar_estado_admision(archivo.admision)
            return True
        except Exception as e:
            logger.error("Error en update_estado_archivo", exc_info=True)
            return False

    @staticmethod
    def verificar_estado_admision(admision):
        try:
            archivos = ArchivoAdmision.objects.filter(admision=admision).only("estado")

            if admision.estado_id != 3:
                if archivos.exists() and all(
                    archivo.estado == "Aceptado" for archivo in archivos
                ):
                    if admision.estado_id != 2:
                        admision.estado_id = 2
                        admision.save()
        except Exception as e:
            logger.error(
                "Error en verificar_estado_admision",
                exc_info=True,
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
        except Exception as e:
            logger.error(
                "Error en get_dupla_grupo_por_usuario",
                exc_info=True,
            )
            return "Otro"

    @staticmethod
    def get_admision(admision_id):
        try:
            return get_object_or_404(Admision, pk=admision_id)
        except Exception as e:
            logger.error("Error en get_admision", exc_info=True)
            return None

    @staticmethod
    def marcar_como_enviado_a_legales(admision, usuario=None):
        try:
            if not admision.enviado_legales:
                admision.enviado_legales = True
                admision.save()
                return True
            return False
        except Exception as e:
            logger.error(
                "Error en marcar_como_enviado_a_legales",
                exc_info=True,
            )
            return False

    @staticmethod
    def marcar_como_enviado_a_acompaniamiento(admision, usuario=None):
        try:
            if not admision.enviado_acompaniamiento:
                admision.enviado_acompaniamiento = True
                admision.save()
                return True
            return False
        except Exception as e:
            logger.error(
                "Error en marcar_como_enviado_a_acompaniamiento",
                exc_info=True,
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
        except Exception as e:
            logger.error(
                "Error en marcar_como_documentacion_rectificada",
                exc_info=True,
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
        except Exception as e:
            logger.error("Error en comenzar_acompanamiento", exc_info=True)
            return None

    @staticmethod
    def get_admision_context(admision_id):
        try:
            admision = get_object_or_404(Admision, id=admision_id)
            return {"admision": admision}
        except Exception as e:
            logger.error("Error en get_admision_context", exc_info=True)
            return {}

    @staticmethod
    def get_admision_instance(admision_id):
        try:
            return get_object_or_404(Admision, id=admision_id)
        except Exception as e:
            logger.error("Error en get_admision_instance", exc_info=True)
            return None
