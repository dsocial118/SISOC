from admisiones.models.admisiones import Admision
from acompanamientos.models.acompanamiento import InformacionRelevante, Prestacion

class AcompanamientoService:

    @staticmethod
    def importar_datos_desde_admision(comedor):
        # Obtener la admisión del comedor
        admision = Admision.objects.filter(comedor=comedor).first()
        if not admision:
            raise ValueError("No se encontró una admisión para este comedor.")

        # Crear o actualizar la información relevante
        InformacionRelevante.objects.update_or_create(
            comedor=comedor,
            defaults={
                "numero_expediente": admision.numero_expediente,
                "numero_resolucion": admision.numero_resolucion,
                "vencimiento_mandato": admision.vencimiento_mandato,
                "if_relevamiento": admision.if_relevamiento,
            },
        )

        # Importar las prestaciones
        prestaciones_admision = admision.prestaciones.all()
        Prestacion.objects.filter(comedor=comedor).delete()  # Limpiar prestaciones previas
        for prestacion in prestaciones_admision:
            Prestacion.objects.create(
                comedor=comedor,
                dia=prestacion.dia,
                desayuno=prestacion.desayuno,
                almuerzo=prestacion.almuerzo,
                merienda=prestacion.merienda,
                cena=prestacion.cena,
            )