"""Cierre automático de comisiones cuya fecha de fin ya pasó.

Las comisiones no cambian de estado solas: este servicio concentra la regla
que usa el management command `cerrar_comisiones_vencidas` (pensado para
correr por cron diario) para cerrar las que quedaron con fecha de fin
vencida. Complementa el bloqueo de inscripciones de
`InscripcionService._comision_vencida`.
"""

from django.utils import timezone

from VAT.models import Comision, ComisionCurso

# "suspendida" es una decisión manual deliberada: no se cierra sola.
ESTADOS_COMISION_CERRABLES = ("planificada", "activa")


class CierreComisionService:
    """Cierra comisiones operativas y de oferta institucional vencidas."""

    @staticmethod
    def comisiones_curso_vencidas(hoy=None):
        hoy = hoy or timezone.localdate()
        return ComisionCurso.objects.filter(
            estado__in=ESTADOS_COMISION_CERRABLES,
            fecha_fin__lt=hoy,
        )

    @staticmethod
    def comisiones_oferta_vencidas(hoy=None):
        hoy = hoy or timezone.localdate()
        return Comision.objects.filter(
            estado__in=ESTADOS_COMISION_CERRABLES,
            fecha_fin__lt=hoy,
        )

    @staticmethod
    def cerrar_comisiones_vencidas(hoy=None):
        hoy = hoy or timezone.localdate()
        # .update() no dispara auto_now: fecha_modificacion se setea explícito.
        ahora = timezone.now()
        cerradas_curso = CierreComisionService.comisiones_curso_vencidas(hoy).update(
            estado="cerrada",
            fecha_modificacion=ahora,
        )
        cerradas_oferta = CierreComisionService.comisiones_oferta_vencidas(hoy).update(
            estado="cerrada",
            fecha_modificacion=ahora,
        )
        return {
            "comisiones_curso": cerradas_curso,
            "comisiones_oferta": cerradas_oferta,
        }
