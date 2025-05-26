from admisiones.models.admisiones import Admision
from acompanamientos.models.hitos import Hitos, CompararHitosIntervenciones
from acompanamientos.models.acompanamiento import InformacionRelevante, Prestacion
from intervenciones.models.intervenciones import Intervencion, SubIntervencion


class AcompanamientoService:
    @staticmethod
    def crear_hitos(intervenciones: Intervencion):
        # Verificar si ya existe un registro de hitos para el comedor
        hitos_existente = Hitos.objects.filter(comedor=intervenciones.comedor).first()
        if intervenciones.subintervencion is None:
            # Si no hay subintervención, crea el nombre vacío
            intervenciones.subintervencion = SubIntervencion()
            intervenciones.subintervencion.nombre = ""
        # Obtener los hitos a actualizar basados en la intervención y subintervención
        hitos_a_actualizar = CompararHitosIntervenciones.objects.filter(
            intervencion=intervenciones.tipo_intervencion.nombre,
            subintervencion=intervenciones.subintervencion.nombre,
        )

        if hitos_existente:
            # Actualizar los campos correspondientes en el modelo Hitos
            for hito in hitos_a_actualizar:
                for field in Hitos._meta.fields:
                    if field.verbose_name == hito.hito:
                        setattr(hitos_existente, field.name, True)
            hitos_existente.save()
        else:
            # Crear un nuevo registro de Hitos
            nuevo_hito = Hitos.objects.create(comedor=intervenciones.comedor)
            for hito in hitos_a_actualizar:
                for field in Hitos._meta.fields:
                    if field.verbose_name == hito.hito:
                        setattr(nuevo_hito, field.name, True)
            nuevo_hito.save()

    @staticmethod
    def obtener_hitos(comedor):
        # Obtener los hitos del comedor
        return Hitos.objects.filter(comedor=comedor).first()

    @staticmethod
    def importar_datos_desde_admision(comedor):
        admision = Admision.objects.filter(comedor=comedor).first()
        if not admision:
            raise ValueError("No se encontró una admisión para este comedor.")
        InformacionRelevante.objects.update_or_create(
            comedor=comedor,
            defaults={
                "numero_expediente": admision.numero_expediente,
                "numero_resolucion": admision.numero_resolucion,
                "vencimiento_mandato": admision.vencimiento_mandato,
                "if_relevamiento": admision.if_relevamiento,
            },
        )

        prestaciones_admision = admision.prestaciones.all()
        Prestacion.objects.filter(comedor=comedor).delete()
        for prestacion in prestaciones_admision:
            Prestacion.objects.create(
                comedor=comedor,
                dia=prestacion.dia,
                desayuno=prestacion.desayuno,
                almuerzo=prestacion.almuerzo,
                merienda=prestacion.merienda,
                cena=prestacion.cena,
            )
