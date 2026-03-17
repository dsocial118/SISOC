"""
Lógica de generación y regeneración de encuentros para ActividadCentro.

Genera una instancia de Encuentro por cada ocurrencia de los días
configurados en la actividad, entre fecha_inicio y fecha_fin.
"""

from datetime import timedelta

# Mapeo de Dia.nombre (core) a Python weekday() — Lunes=0, Domingo=6
DIA_A_WEEKDAY = {
    "lunes": 0,
    "martes": 1,
    "miércoles": 2,
    "miercoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sábado": 5,
    "sabado": 5,
    "domingo": 6,
}


class EncuentroService:
    @staticmethod
    def generar_encuentros(actividad_centro):
        """
        Genera todos los encuentros para una actividad nueva.
        Requiere que actividad_centro tenga fecha_inicio, fecha_fin y dias configurados.
        No hace nada si falta alguno de esos datos.
        Retorna la cantidad de encuentros creados.
        """
        from VAT.models import Encuentro

        if not actividad_centro.fecha_inicio or not actividad_centro.fecha_fin:
            return 0

        weekdays = EncuentroService._obtener_weekdays(actividad_centro)
        if not weekdays:
            return 0

        encuentros = EncuentroService._construir_encuentros(
            actividad_centro, weekdays, fechas_excluidas=set()
        )
        Encuentro.objects.bulk_create(encuentros)
        return len(encuentros)

    @staticmethod
    def regenerar_encuentros(actividad_centro):
        """
        En actualización: elimina encuentros programados sin asistencias y regenera.
        Los encuentros con asistencias ya registradas se preservan.
        Retorna la cantidad de encuentros nuevos creados.
        """
        from VAT.models import Asistencia, Encuentro

        if not actividad_centro.fecha_inicio or not actividad_centro.fecha_fin:
            return 0

        weekdays = EncuentroService._obtener_weekdays(actividad_centro)
        if not weekdays:
            return 0

        # Fechas de encuentros que ya tienen asistencias → no tocar
        ids_con_asistencia = Asistencia.objects.filter(
            encuentro__actividad_centro=actividad_centro
        ).values_list("encuentro_id", flat=True).distinct()

        fechas_preservadas = set(
            Encuentro.objects.filter(
                actividad_centro=actividad_centro,
                id__in=ids_con_asistencia,
            ).values_list("fecha", flat=True)
        )

        # Eliminar encuentros programados que no tienen asistencias
        Encuentro.objects.filter(
            actividad_centro=actividad_centro,
            estado="programado",
        ).exclude(id__in=ids_con_asistencia).delete()

        # Regenerar solo las fechas no preservadas
        nuevos = EncuentroService._construir_encuentros(
            actividad_centro, weekdays, fechas_excluidas=fechas_preservadas
        )
        Encuentro.objects.bulk_create(nuevos, ignore_conflicts=True)

        # Renumerar todos los encuentros de la actividad por fecha
        EncuentroService._renumerar(actividad_centro)

        return len(nuevos)

    # ── helpers privados ──────────────────────────────────────────────────────

    @staticmethod
    def _obtener_weekdays(actividad_centro):
        """Convierte los Dia M2M de la actividad en un set de weekday() de Python."""
        nombres = actividad_centro.dias.values_list("nombre", flat=True)
        weekdays = set()
        for nombre in nombres:
            wd = DIA_A_WEEKDAY.get(nombre.lower().strip())
            if wd is not None:
                weekdays.add(wd)
        return weekdays

    @staticmethod
    def _construir_encuentros(actividad_centro, weekdays, fechas_excluidas):
        """
        Devuelve una lista de instancias Encuentro (sin guardar) para cada
        fecha en el rango que coincida con los días de la semana solicitados,
        excluyendo fechas ya existentes.
        """
        from VAT.models import Encuentro

        encuentros = []
        numero = (
            Encuentro.objects.filter(actividad_centro=actividad_centro).count() + 1
        )
        fecha = actividad_centro.fecha_inicio

        while fecha <= actividad_centro.fecha_fin:
            if fecha.weekday() in weekdays and fecha not in fechas_excluidas:
                encuentros.append(
                    Encuentro(
                        actividad_centro=actividad_centro,
                        numero_encuentro=numero,
                        fecha=fecha,
                        hora_inicio=actividad_centro.horariosdesde,
                        hora_fin=actividad_centro.horarioshasta,
                        estado="programado",
                    )
                )
                numero += 1
            fecha += timedelta(days=1)

        return encuentros

    @staticmethod
    def _renumerar(actividad_centro):
        """Reasigna numero_encuentro secuencial ordenado por fecha."""
        from VAT.models import Encuentro

        encuentros = list(
            Encuentro.objects.filter(actividad_centro=actividad_centro).order_by("fecha")
        )
        for i, enc in enumerate(encuentros, start=1):
            if enc.numero_encuentro != i:
                enc.numero_encuentro = i
        Encuentro.objects.bulk_update(encuentros, ["numero_encuentro"])


class AsistenciaService:
    @staticmethod
    def registrar_bulk(encuentro, datos, usuario):
        """
        Registra o actualiza la asistencia de todos los participantes en un encuentro.

        datos: lista de dicts {"participante_id": int, "estado": str, "observaciones": str}

        Marca el encuentro como "realizado" al finalizar.
        """
        from django.db import transaction
        from VAT.models import Asistencia

        with transaction.atomic():
            for dato in datos:
                Asistencia.objects.update_or_create(
                    encuentro=encuentro,
                    participante_id=dato["participante_id"],
                    defaults={
                        "estado": dato["estado"],
                        "observaciones": dato.get("observaciones", ""),
                        "registrado_por": usuario,
                    },
                )
            encuentro.estado = "realizado"
            encuentro.save(update_fields=["estado"])

    @staticmethod
    def obtener_asistencias_para_encuentro(encuentro):
        """
        Retorna un dict {participante_id: Asistencia} para un encuentro.
        """
        from VAT.models import Asistencia

        return {
            a.participante_id: a
            for a in Asistencia.objects.filter(encuentro=encuentro).select_related(
                "registrado_por"
            )
        }
