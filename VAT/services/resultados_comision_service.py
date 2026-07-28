"""Carga de resultados de aprobación y acta de cierre de una comisión de curso.

Concentra las reglas de la pestaña "Resultados" del detalle de comisión:
qué alumnos son calificables, cómo se persiste el acta y cómo impacta la
calificación en el estado de la inscripción.
"""

from datetime import date

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date

from VAT.models import ActaCierreComision, Inscripcion
from VAT.services.inscripcion_service import InscripcionService

# Sólo la inscripción confirmada (`inscripta`) habilita la carga de resultado.
# `completada` se incluye porque calificar mueve la inscripción a ese estado:
# sin esto los alumnos ya calificados desaparecerían del listado y el resultado
# no podría corregirse después de guardado.
ESTADO_ALUMNO_A_CALIFICAR = "inscripta"
ESTADO_ALUMNO_CALIFICADO = "completada"
ESTADOS_ALUMNOS_CALIFICABLES = (
    ESTADO_ALUMNO_A_CALIFICAR,
    ESTADO_ALUMNO_CALIFICADO,
)

RESULTADOS_VALIDOS = dict(Inscripcion.RESULTADO_FINAL_CHOICES)

MENSAJE_PROFESOR_REQUERIDO = "Seleccioná el profesor a cargo para guardar el acta."
MENSAJE_FECHA_FIN_REQUERIDA = "Indicá la fecha de fin para guardar el acta."
MENSAJE_FECHA_FIN_INVALIDA = "La fecha de fin del acta no es válida."
MENSAJE_PROFESOR_OTRO_CENTRO = (
    "El profesor seleccionado no pertenece al centro de la comisión."
)


class ResultadosComisionService:
    """Persiste calificaciones de curso y datos del acta de cierre."""

    @staticmethod
    def alumnos_calificables(comision_curso):
        """Inscripciones que aparecen en el listado de calificación."""
        return (
            Inscripcion.objects.filter(
                comision_curso=comision_curso,
                estado__in=ESTADOS_ALUMNOS_CALIFICABLES,
            )
            .select_related("ciudadano")
            .order_by("ciudadano__apellido", "ciudadano__nombre", "pk")
        )

    @staticmethod
    def resumen(inscripciones):
        """Contadores de las cards de resumen. Acepta lista o queryset."""
        inscripciones = list(inscripciones)
        aprobados = sum(
            1
            for inscripcion in inscripciones
            if inscripcion.resultado_final == Inscripcion.RESULTADO_APROBADO
        )
        desaprobados = sum(
            1
            for inscripcion in inscripciones
            if inscripcion.resultado_final == Inscripcion.RESULTADO_DESAPROBADO
        )
        return {
            "aprobados": aprobados,
            "desaprobados": desaprobados,
            "sin_calificar": len(inscripciones) - aprobados - desaprobados,
            "inscriptos": len(inscripciones),
        }

    @staticmethod
    def _normalizar_fecha_fin(fecha_fin):
        """
        Acepta `date` o string ISO y devuelve un `date`.

        La vista recibe el valor crudo del POST. Asignar un string invalido al
        DateField haria estallar el save con `ValidationError`, que no es
        `ValueError` y por lo tanto no lo atrapa el manejo de errores de la
        vista: terminaba en 500 en vez de un mensaje al usuario.
        """
        if isinstance(fecha_fin, date):
            return fecha_fin
        parseada = parse_date(str(fecha_fin).strip())
        if parseada is None:
            raise ValueError(MENSAJE_FECHA_FIN_INVALIDA)
        return parseada

    @staticmethod
    def _validar_acta(*, comision_curso, profesor, fecha_fin):
        if profesor is None:
            raise ValueError(MENSAJE_PROFESOR_REQUERIDO)
        if not fecha_fin:
            raise ValueError(MENSAJE_FECHA_FIN_REQUERIDA)
        if profesor.centro_id != comision_curso.curso.centro_id:
            raise ValueError(MENSAJE_PROFESOR_OTRO_CENTRO)
        return ResultadosComisionService._normalizar_fecha_fin(fecha_fin)

    @staticmethod
    def _guardar_acta(
        *, comision_curso, profesor, fecha_fin, numero_acta, usuario
    ):  # pylint: disable=too-many-arguments
        acta, _ = ActaCierreComision.objects.update_or_create(
            comision_curso=comision_curso,
            defaults={
                "profesor": profesor,
                "fecha_fin": fecha_fin,
                "numero_acta": (numero_acta or "").strip() or None,
                "registrado_por": usuario,
            },
        )
        return acta

    @staticmethod
    def _aplicar_resultado(*, inscripcion, resultado, usuario, ahora):
        inscripcion.resultado_final = resultado
        inscripcion.resultado_registrado_por = usuario
        inscripcion.resultado_fecha = ahora
        inscripcion.save(
            update_fields=[
                "resultado_final",
                "resultado_registrado_por",
                "resultado_fecha",
                "fecha_modificacion",
            ]
        )
        # Calificar cierra el ciclo de la inscripción: aprobado o desaprobado,
        # el alumno cursó y finalizó. Se delega en InscripcionService para no
        # duplicar las reglas de transición de estado.
        if inscripcion.estado != ESTADO_ALUMNO_CALIFICADO:
            InscripcionService.actualizar_estado_inscripcion(
                inscripcion=inscripcion,
                nuevo_estado=ESTADO_ALUMNO_CALIFICADO,
                usuario=usuario,
            )

    @staticmethod
    @transaction.atomic
    def guardar_resultados(  # pylint: disable=too-many-arguments
        *,
        comision_curso,
        profesor,
        fecha_fin,
        numero_acta,
        resultados,
        usuario,
    ):
        """
        Persiste el acta y las calificaciones recibidas.

        `resultados` es un dict {inscripcion_id: "aprobado"|"desaprobado"}.
        Las claves ausentes o con valor inválido se ignoran: un guardado
        parcial nunca borra un resultado ya cargado.
        """
        fecha_fin = ResultadosComisionService._validar_acta(
            comision_curso=comision_curso,
            profesor=profesor,
            fecha_fin=fecha_fin,
        )

        acta = ResultadosComisionService._guardar_acta(
            comision_curso=comision_curso,
            profesor=profesor,
            fecha_fin=fecha_fin,
            numero_acta=numero_acta,
            usuario=usuario,
        )

        ahora = timezone.now()
        calificados = 0
        # Se recorre el conjunto calificable — no las claves recibidas — para
        # que un id ajeno a la comisión no pueda tocar otra inscripción.
        for inscripcion in ResultadosComisionService.alumnos_calificables(
            comision_curso
        ):
            resultado = resultados.get(inscripcion.pk)
            if resultado not in RESULTADOS_VALIDOS:
                continue
            if inscripcion.resultado_final == resultado:
                continue
            ResultadosComisionService._aplicar_resultado(
                inscripcion=inscripcion,
                resultado=resultado,
                usuario=usuario,
                ahora=ahora,
            )
            calificados += 1

        return {"acta": acta, "calificados": calificados}
