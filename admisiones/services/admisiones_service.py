import os
from django.conf import settings
from django.db import models
from django.db import transaction
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
    InformeComplementario,
)
from admisiones.forms.admisiones_forms import (
    CaratularForm,
)
from acompanamientos.acompanamiento_service import AcompanamientoService
from comedores.models import Comedor
from django.db.models import Q
from django.shortcuts import get_object_or_404

import logging


logger = logging.getLogger("django")


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

        except Exception:

            logger.exception("Error en get_comedores_with_admision")

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

        except Exception:

            logger.exception(
                "Error en get_comedores_filtrados",
                extra={"query": query},
            )

            return Comedor.objects.none()

    @staticmethod
    def get_admision_create_context(pk):

        try:

            comedor = get_object_or_404(Comedor, pk=pk)

            convenios = TipoConvenio.objects.all()

            return {
                "comedor": comedor,
                "convenios": convenios,
                "es_crear": True,
                "documentos": [],
                "documentos_personalizados": [],
                "resumen_estados": AdmisionService._resumen_vacio(),
                "obligatorios_totales": 0,
                "obligatorios_completos": 0,
                "stats": AdmisionService._stats_from_resumen(
                    AdmisionService._resumen_vacio(), 0, 0
                ),
            }

        except Exception:

            logger.exception(
                "Error en get_admision_create_context",
                extra={"comedor_pk": pk},
            )

            return {}

    @staticmethod
    def create_admision(comedor_pk, tipo_convenio_id):
        try:
            # Buscar comedor
            comedor = Comedor.objects.filter(pk=comedor_pk).first()
            if not comedor:
                logger.warning(
                    "Comedor no encontrado", extra={"comedor_pk": comedor_pk}
                )
                return None

            # Buscar tipo de convenio
            tipo_convenio = TipoConvenio.objects.filter(pk=tipo_convenio_id).first()
            if not tipo_convenio:
                logger.warning(
                    "TipoConvenio no encontrado",
                    extra={"tipo_convenio_id": tipo_convenio_id},
                )
                return None

            # Buscar estado inicial (Pendiente)
            estado = EstadoAdmision.objects.filter(nombre__iexact="Pendiente").first()
            if not estado:
                logger.error("EstadoAdmision 'Pendiente' no existe en la BD")
                return None

            # Crear admisión
            return Admision.objects.create(
                comedor=comedor,
                tipo_convenio=tipo_convenio,
                estado=estado,
            )

        except Exception:
            logger.exception(
                "Error inesperado en create_admision",
                extra={
                    "comedor_pk": comedor_pk,
                    "tipo_convenio_id": tipo_convenio_id,
                },
            )
            return None

    @staticmethod
    def get_admision_update_context(admision):
        try:
            documentaciones = (
                Documentacion.objects.filter(models.Q(convenios=admision.tipo_convenio))
                .distinct()
                .order_by("-obligatorio", "nombre")
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
                "documentos_personalizados": documentos_personalizados_info,
                "comedor": comedor,
                "convenios": convenios,
                "caratular_form": caratular_form,
                "informe_tecnico": informe_tecnico,
                "anexo": anexo,
                "pdf": pdf,
                "informes_complementarios": informes_complementarios,
                "resumen_estados": resumen_estados,
                "obligatorios_totales": obligatorios_totales,
                "obligatorios_completos": obligatorios_completos,
                "stats": stats,
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

            admision.save()

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
    def handle_file_upload(admision_id, documentacion_id, archivo):

        try:

            admision = get_object_or_404(Admision, pk=admision_id)

            documentacion = get_object_or_404(Documentacion, pk=documentacion_id)

            return ArchivoAdmision.objects.update_or_create(
                admision=admision,
                documentacion=documentacion,
                defaults={
                    "archivo": archivo,
                    "estado": "Documento adjunto",
                    "nombre_personalizado": None,
                },
            )

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

            estado_actual = (
                getattr(getattr(admision, "estado", None), "nombre", "") or ""
            )

            if estado_actual.lower() == "finalizada":

                return None, "La admision esta finalizada."

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

            AdmisionService.verificar_estado_admision(archivo.admision)

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

                if archivos.exists() and all(
                    archivo.estado == "Aceptado" for archivo in archivos
                ):

                    if admision.estado_id != 2:

                        admision.estado_id = 2

                        admision.save()

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

                admision.save()

                return True

            return False

        except Exception:

            logger.exception(
                "Error en marcar_como_enviado_a_legales",
                extra={"admision_pk": admision.pk},
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
