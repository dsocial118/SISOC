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
    def get_comedores_with_admision():
        admision_subquery = Admision.objects.filter(comedor=OuterRef("pk")).values(
            "id"
        )[:1]
        return Comedor.objects.annotate(admision_id=Subquery(admision_subquery))

    @staticmethod
    def get_admision_create_context(pk):
        comedor = get_object_or_404(Comedor, pk=pk)
        convenios = TipoConvenio.objects.all()

        return {"comedor": comedor, "convenios": convenios, "es_crear": True}

    @staticmethod
    def create_admision(comedor_pk, tipo_convenio_id):
        comedor = get_object_or_404(Comedor, pk=comedor_pk)
        tipo_convenio = get_object_or_404(TipoConvenio, pk=tipo_convenio_id)

        return Admision.objects.create(comedor=comedor, tipo_convenio=tipo_convenio)

    @staticmethod
    def get_admision_update_context(admision):
        comedor = Comedor.objects.get(pk=admision.comedor_id)
        convenios = TipoConvenio.objects.all()

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

        return {
            "documentos": documentos_info,
            "comedor": comedor,
            "convenios": convenios,
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
