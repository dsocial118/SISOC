"""
Generación y regeneración de SesionComision a partir de los ComisionHorario.

Por cada ComisionHorario (día + hora_desde/hasta) se genera una SesionComision
por cada ocurrencia de ese día dentro del rango fecha_inicio/fecha_fin de la Comision.

Ejemplo:
  Comision: 22/03/2026 → 22/04/2026
  Horario: Lunes 10:00-12:00
  Resultado: 5 sesiones (23/03, 30/03, 06/04, 13/04, 20/04... según el rango)
"""

from datetime import timedelta

# Mapeo nombre de Dia (core) → weekday() de Python. Lunes=0, Domingo=6
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


class SesionComisionService:

    @staticmethod
    def _comision_filter(comision):
        if getattr(comision, "curso_id", None):
            return {"comision_curso": comision}
        return {"comision": comision}

    @staticmethod
    def generar_para_horario(horario):
        """
        Genera todas las sesiones para un ComisionHorario nuevo.
        Retorna la cantidad de sesiones creadas.
        """
        from VAT.models import SesionComision

        comision = horario.entidad_comision
        if not comision.fecha_inicio or not comision.fecha_fin:
            return 0

        weekday = SesionComisionService._weekday(horario)
        if weekday is None:
            return 0

        sesiones = SesionComisionService._construir(
            comision, horario, weekday, fechas_excluidas=set()
        )
        SesionComision.objects.bulk_create(sesiones, ignore_conflicts=True)
        SesionComisionService._renumerar(comision)
        return len(sesiones)

    @staticmethod
    def regenerar_para_horario(horario):
        """
        En actualización de un horario: elimina las sesiones programadas de ese
        horario y regenera. Las sesiones realizadas/canceladas se preservan.
        Retorna la cantidad de sesiones nuevas creadas.
        """
        from VAT.models import SesionComision

        comision = horario.entidad_comision
        if not comision.fecha_inicio or not comision.fecha_fin:
            return 0

        weekday = SesionComisionService._weekday(horario)
        if weekday is None:
            return 0

        # Preservar fechas con sesiones ya realizadas o canceladas
        fechas_preservadas = set(
            SesionComision.objects.filter(
                horario=horario,
            )
            .exclude(estado="programada")
            .values_list("fecha", flat=True)
        )

        # Eliminar solo las programadas
        SesionComision.objects.filter(horario=horario, estado="programada").delete()

        # Regenerar
        sesiones = SesionComisionService._construir(
            comision, horario, weekday, fechas_excluidas=fechas_preservadas
        )
        SesionComision.objects.bulk_create(sesiones, ignore_conflicts=True)
        SesionComisionService._renumerar(comision)
        return len(sesiones)

    @staticmethod
    def regenerar_para_comision(comision):
        """
        Regenera todas las sesiones de una comisión cuando cambian las fechas.
        Itera sobre todos sus ComisionHorario activos.
        """
        total = 0
        for horario in comision.horarios.filter(vigente=True):
            total += SesionComisionService.regenerar_para_horario(horario)
        return total

    @staticmethod
    def eliminar_para_horario(horario):
        """Elimina sesiones programadas de un horario que se va a borrar."""
        from VAT.models import SesionComision

        deleted, _ = SesionComision.objects.filter(
            horario=horario, estado="programada"
        ).delete()
        SesionComisionService._renumerar(horario.entidad_comision)
        return deleted

    # ── helpers privados ─────────────────────────────────────────────────────

    @staticmethod
    def _weekday(horario):
        nombre = horario.dia_semana.nombre.lower().strip()
        return DIA_A_WEEKDAY.get(nombre)

    @staticmethod
    def _construir(comision, horario, weekday, fechas_excluidas):
        from VAT.models import SesionComision

        # Número base para continuar la secuencia
        base = (
            SesionComision.objects.filter(
                **SesionComisionService._comision_filter(comision)
            ).count()
            + 1
        )

        sesiones = []
        fecha = comision.fecha_inicio
        numero = base

        while fecha <= comision.fecha_fin:
            if fecha.weekday() == weekday and fecha not in fechas_excluidas:
                sesiones.append(
                    SesionComision(
                        horario=horario,
                        numero_sesion=numero,
                        fecha=fecha,
                        estado="programada",
                        **SesionComisionService._comision_filter(comision),
                    )
                )
                numero += 1
            fecha += timedelta(days=1)

        return sesiones

    @staticmethod
    def _renumerar(comision):
        """Reasigna numero_sesion secuencial ordenado por fecha y hora."""
        from VAT.models import SesionComision

        sesiones = list(
            SesionComision.objects.filter(
                **SesionComisionService._comision_filter(comision)
            ).order_by("fecha", "horario__hora_desde")
        )
        for i, s in enumerate(sesiones, start=1):
            s.numero_sesion = i
        SesionComision.objects.bulk_update(sesiones, ["numero_sesion"])
