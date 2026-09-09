"""
Servicio de validación de edad para menores y responsables en celiaquía.
Implementa los requerimientos:
- Responsable menor de 18 años: BLOQUEO
- Beneficiario menor sin responsable: BLOQUEO
"""

from datetime import date
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger("django")


class ValidacionEdadService:
    """Validaciones de edad para beneficiarios y responsables."""

    @staticmethod
    def calcular_edad(fecha_nacimiento):
        """Calcula la edad en años a partir de una fecha de nacimiento."""
        if not fecha_nacimiento:
            return None
        try:
            hoy = date.today()
            return (
                hoy.year
                - fecha_nacimiento.year
                - (
                    (hoy.month, hoy.day)
                    < (fecha_nacimiento.month, fecha_nacimiento.day)
                )
            )
        except Exception as e:
            logger.warning("Error calculando edad: %s", e)
            return None

    @staticmethod
    def es_menor_de_edad(fecha_nacimiento):
        """Indica si la fecha corresponde a un menor de 18 años.

        Sin fecha de nacimiento se asume mayor de edad, en linea con
        ``validar_beneficiario_menor_con_responsable`` y con el calculo de
        archivos requeridos de ``LegajoService``: un dato faltante no debe
        bloquear el expediente.
        """
        edad = ValidacionEdadService.calcular_edad(fecha_nacimiento)
        return edad is not None and edad < 18

    @staticmethod
    def validar_responsable_mayor_edad(fecha_nacimiento_responsable):
        """
        Requerimiento 1: Responsable menor de 18 años (BLOQUEO)

        Si una persona tiene el rol de Responsable y su edad es menor a 18 años,
        se rechaza la fila y se marca como error.

        Args:
            fecha_nacimiento_responsable: fecha de nacimiento del responsable

        Raises:
            ValidationError: si el responsable es menor de 18 años
        """
        if not fecha_nacimiento_responsable:
            return True

        edad = ValidacionEdadService.calcular_edad(fecha_nacimiento_responsable)

        if edad is None:
            return True

        if edad < 18:
            raise ValidationError(
                f"El responsable no puede ser menor de 18 años (edad: {edad})"
            )

        return True

    @staticmethod
    def validar_beneficiario_menor_con_responsable(
        fecha_nacimiento_beneficiario, tiene_responsable
    ):
        """
        Requerimiento 2: Beneficiario menor sin responsable (BLOQUEO)

        Si el beneficiario es menor de 18 años, debe existir un responsable asociado.
        Si no hay responsable, se rechaza la fila.

        Args:
            fecha_nacimiento_beneficiario: fecha de nacimiento del beneficiario
            tiene_responsable: bool indicando si hay responsable asociado

        Raises:
            ValidationError: si el beneficiario es menor y no tiene responsable
        """
        if not fecha_nacimiento_beneficiario:
            return True

        edad = ValidacionEdadService.calcular_edad(fecha_nacimiento_beneficiario)

        if edad is None:
            return True

        if edad < 18 and not tiene_responsable:
            raise ValidationError(
                "El beneficiario menor de 18 años debe tener un responsable"
            )

        return True

    @staticmethod
    def validar_relacion_responsable_beneficiario(
        fecha_nacimiento_responsable, fecha_nacimiento_beneficiario
    ):
        """
        Validación adicional: responsable no puede ser más joven que beneficiario.

        Args:
            fecha_nacimiento_responsable: fecha de nacimiento del responsable
            fecha_nacimiento_beneficiario: fecha de nacimiento del beneficiario

        Raises:
            ValidationError: si el responsable es más joven que el beneficiario
        """
        if not fecha_nacimiento_responsable or not fecha_nacimiento_beneficiario:
            return True

        edad_responsable = ValidacionEdadService.calcular_edad(
            fecha_nacimiento_responsable
        )
        edad_beneficiario = ValidacionEdadService.calcular_edad(
            fecha_nacimiento_beneficiario
        )

        if edad_responsable is None or edad_beneficiario is None:
            return True

        if edad_responsable < edad_beneficiario:
            raise ValidationError(
                f"El responsable ({edad_responsable} años) no puede ser más joven "
                f"que el beneficiario ({edad_beneficiario} años)"
            )

        return True

    @staticmethod
    def menores_sin_responsable(expediente, excluir_legajo_ids=None):
        """Legajos de menores de 18 sin un adulto responsable en el expediente.

        La relacion familiar vive en ``ciudadanos.GrupoFamiliar`` y cuelga del
        ciudadano, no del legajo: al dar de baja el legajo del responsable el
        vinculo sobrevive intacto y el menor queda sin responsable *dentro del
        expediente* sin que ninguna validacion lo note. Por eso el corte es
        "el responsable tiene legajo vivo en este expediente", no "existe el
        vinculo".

        ``excluir_legajo_ids`` simula la baja de esos legajos, para poder
        anticipar el efecto de una eliminacion antes de ejecutarla.

        Se considera responsable valido a cualquier ciudadano vinculado como
        cuidador principal que tenga legajo vivo en el expediente, sin exigir
        un rol determinado: la validacion bloquea el envio y un falso positivo
        frenaria un expediente legitimo.
        """
        from celiaquia.services.familia_service import (  # pylint: disable=import-outside-toplevel
            FamiliaService,
        )

        excluidos = set(excluir_legajo_ids or ())

        # Igual que LegajoService, se tolera un expediente sin el manager de
        # legajos (stubs de tests unitarios): sin legajos no hay nada que validar.
        qs = getattr(expediente, "expediente_ciudadanos", None)
        if qs is None:
            return []
        if hasattr(qs, "select_related"):
            qs = qs.select_related("ciudadano")
        legajos = list(qs.all() if hasattr(qs, "all") else qs)
        legajos = [leg for leg in legajos if leg.pk not in excluidos]
        if not legajos:
            return []

        menores = [
            leg
            for leg in legajos
            if ValidacionEdadService.es_menor_de_edad(
                getattr(leg.ciudadano, "fecha_nacimiento", None)
            )
        ]
        if not menores:
            return []

        ciudadanos_vivos = {leg.ciudadano_id for leg in legajos}
        responsables_por_hijo = FamiliaService.obtener_responsables_por_hijo(
            [leg.ciudadano_id for leg in menores]
        )

        huerfanos = []
        for leg in menores:
            responsables = responsables_por_hijo.get(leg.ciudadano_id, [])
            tiene_responsable = any(
                resp.id in ciudadanos_vivos and resp.id != leg.ciudadano_id
                for resp in responsables
            )
            if not tiene_responsable:
                huerfanos.append(leg)
        return huerfanos

    @staticmethod
    def menores_que_quedarian_sin_responsable(legajo):
        """Menores que se quedarian sin responsable si se elimina ``legajo``.

        Devuelve solo el delta que provoca esa baja: los menores que ya estaban
        sin responsable antes no se le atribuyen a esta eliminacion.
        """
        expediente = legajo.expediente
        previos = {
            leg.pk for leg in ValidacionEdadService.menores_sin_responsable(expediente)
        }
        return [
            leg
            for leg in ValidacionEdadService.menores_sin_responsable(
                expediente, excluir_legajo_ids={legajo.pk}
            )
            if leg.pk not in previos
        ]

    @staticmethod
    def describir_legajos(legajos, limit=10):
        """Formatea legajos como "Apellido, Nombre (CUIL 20...)" para mensajes."""
        descripciones = []
        for leg in legajos[:limit]:
            apellido = getattr(leg.ciudadano, "apellido", "") or ""
            nombre = getattr(leg.ciudadano, "nombre", "") or ""
            documento = getattr(leg.ciudadano, "documento", "") or "s/d"
            descripciones.append(f"{apellido}, {nombre} (CUIL {documento})")
        restantes = len(legajos) - limit
        if restantes > 0:
            descripciones.append(f"y {restantes} mas")
        return descripciones

    @staticmethod
    def advertencia_por_eliminacion(legajo):
        """Aviso para el preview de baja de un legajo, o ``None`` si no aplica.

        La baja no se bloquea: la provincia puede querer dar de baja al grupo
        familiar completo y bloquearla la dejaria trabada. Se avisa aca y se
        bloquea recien al enviar, igual que la documentacion faltante.
        """
        afectados = ValidacionEdadService.menores_que_quedarian_sin_responsable(legajo)
        if not afectados:
            return None
        return {
            "legajo_ids": [leg.pk for leg in afectados],
            "detalle": ValidacionEdadService.describir_legajos(afectados),
            "mensaje": (
                f"Atencion: al eliminar este legajo quedan {len(afectados)} "
                "menor(es) de edad sin adulto responsable. No vas a poder enviar "
                "el expediente hasta volver a incorporar un responsable o quitar "
                "esos legajos."
            ),
        }

    @staticmethod
    def mensaje_menores_sin_responsable(legajos):
        """Mensaje unico de bloqueo, compartido por la vista y el service."""
        return (
            "No se puede enviar el expediente: hay menores de edad sin adulto "
            "responsable asociado. Volve a incorporar el legajo del responsable "
            "o quita el del menor. Afectados: "
            + "; ".join(ValidacionEdadService.describir_legajos(legajos))
        )
