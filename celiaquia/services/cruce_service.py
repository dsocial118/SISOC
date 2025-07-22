import openpyxl
from django.db import transaction

from celiaquia.models import EstadoExpediente
from celiaquia.models import ArchivoCruce, ResultadoCruce, ExpedienteCiudadano


class CruceService:
    @staticmethod
    @transaction.atomic
    def subir_archivo_cruce(expediente, organismo, tipo, archivo):
        return ArchivoCruce.objects.create(
            expediente=expediente, organismo=organismo, tipo=tipo, archivo=archivo
        )

    @staticmethod
    @transaction.atomic
    def procesar_todos_los_cruces(expediente):
        archivos = ArchivoCruce.objects.filter(expediente=expediente)
        for archivo in archivos:
            wb = openpyxl.load_workbook(archivo.archivo)
            sheet = wb.worksheets[0]
            for row in sheet.iter_rows(min_row=2, values_only=True):
                dni = row[2]
                legajo = ExpedienteCiudadano.objects.get(
                    expediente=expediente, ciudadano__documento=dni
                )
                estado = archivo.tipo  # TipoCruce instance
                ResultadoCruce.objects.create(
                    expediente=expediente,
                    expediente_ciudadano=legajo,
                    organismo=archivo.organismo,
                    estado=estado,
                )
        return True

    @staticmethod
    def finalizar_cruce(expediente):
        estado = EstadoExpediente.objects.get(nombre="CRUCE_FINALIZADO")
        expediente.estado = estado
        expediente.save()
        return expediente
