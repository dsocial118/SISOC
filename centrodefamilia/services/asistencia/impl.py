"""Toma de asistencia de participantes inscritos a una actividad de CDF.

Espeja el flujo de asistencia de VAT (``AsistenciaSesionView``) adaptado a la
estructura de CDF: sin sesiones autogeneradas, la planilla se arma por
(actividad, fecha) sobre los participantes con estado "inscrito".
"""

from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from centrodefamilia.models import AsistenciaActividad, ParticipanteActividad


class AsistenciaActividadService:
    @staticmethod
    def parse_fecha(raw):
        """Normaliza la fecha de la planilla; hoy por defecto.

        Rechaza formatos inválidos y fechas futuras (no se puede tomar
        asistencia por adelantado).
        """
        if not raw:
            fecha = timezone.localdate()
        else:
            try:
                fecha = datetime.strptime(str(raw), "%Y-%m-%d").date()
            except ValueError as exc:
                raise ValidationError("La fecha indicada no es válida.") from exc
        if fecha > timezone.localdate():
            raise ValidationError("No se puede tomar asistencia para una fecha futura.")
        return fecha

    @staticmethod
    def inscritos(actividad_centro):
        return list(
            ParticipanteActividad.objects.filter(
                actividad_centro=actividad_centro,
                estado="inscrito",
            )
            .select_related("ciudadano")
            .order_by("ciudadano__apellido", "ciudadano__nombre")
        )

    @classmethod
    def obtener_planilla(cls, actividad_centro, fecha):
        """Filas (participante, presente) para la planilla de una fecha.

        ``presente`` es ``None`` si aún no hay registro para ese participante.
        """
        participantes = cls.inscritos(actividad_centro)
        existentes = {
            asistencia.participante_id: asistencia
            for asistencia in AsistenciaActividad.objects.filter(
                fecha=fecha,
                participante__in=[p.pk for p in participantes],
            )
        }
        filas = []
        for participante in participantes:
            registro = existentes.get(participante.pk)
            filas.append(
                {
                    "participante": participante,
                    "presente": registro.presente if registro else None,
                }
            )
        return filas

    @classmethod
    def registrar(cls, actividad_centro, fecha, marcas, usuario):
        """Guarda/actualiza la asistencia de la fecha para todos los inscritos.

        ``marcas`` mapea ``participante_id -> "1"|"0"|None`` (valores del POST);
        igual que en VAT, lo no marcado se registra como ausente.
        Devuelve la cantidad de registros guardados.
        """
        participantes = cls.inscritos(actividad_centro)
        with transaction.atomic():
            for participante in participantes:
                presente = marcas.get(participante.pk) == "1"
                AsistenciaActividad.objects.update_or_create(
                    participante=participante,
                    fecha=fecha,
                    defaults={
                        "presente": presente,
                        "registrado_por": usuario,
                    },
                )
        return len(participantes)
