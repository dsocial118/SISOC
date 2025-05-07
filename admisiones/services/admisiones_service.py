import os
from django.conf import settings
from django.db import models
from django.shortcuts import get_object_or_404
from django.db.models import OuterRef, Subquery
from admisiones.models.admisiones import (
    Admision,
    TipoConvenio,
    Documentacion,
    ArchivoAdmision,
)
from comedores.models.comedor import Comedor


class AdmisionService:

    @staticmethod
    def get_comedores_with_admision(user):
        admision_subquery = Admision.objects.filter(
            comedor=OuterRef("pk")
        ).values("id")[:1]

        return Comedor.objects.filter(
            dupla__tecnico=user,
            dupla__estado="Activo"
        ).annotate(
            admision_id=Subquery(admision_subquery)
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

        return Admision.objects.create(comedor=comedor, tipo_convenio=tipo_convenio, estado_id=estado)

    @staticmethod
    def get_admision_update_context(admision):
        documentaciones = Documentacion.objects.filter(
            models.Q(convenios=admision.tipo_convenio)
        ).distinct()

        estado_actualizado = False
        archivos_subidos = ArchivoAdmision.objects.filter(admision=admision)
        if archivos_subidos.exists() and all(archivo.estado == "Aceptado" for archivo in archivos_subidos):
            if admision.estado_id != 2:
                admision.estado_id = 2
                admision.save()
                estado_actualizado = True
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
        return {
            "documentos": documentos_info,
            "comedor": comedor,
            "convenios": convenios,
            "admision_todo_aceptado": estado_actualizado,
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
    def update_estado_archivo(archivo, nuevo_estado):
        if not archivo:
            return False

        # Actualiza el estado del archivo
        archivo.estado = nuevo_estado
        archivo.save()
        return True