import logging

from django.db.models import Q, Exists, OuterRef
from django.db import transaction
from admisiones.models.admisiones import (
    Admision,
    InformeTecnico,
    DocumentosExpediente,
    Anexo,
)
from acompanamientos.models.hitos import Hitos, HitosIntervenciones
from acompanamientos.models.acompanamiento import InformacionRelevante, Prestacion
from duplas.models import Dupla
from intervenciones.models.intervenciones import Intervencion, SubIntervencion
from comedores.models import Comedor

logger = logging.getLogger("django")


class AcompanamientoService:
    @staticmethod
    def crear_hitos(intervenciones: Intervencion):
        """Crear o actualizar los hitos para una intervención.

        Args:
            intervenciones (Intervencion): Intervención a procesar.

        Returns:
            None
        """
        # Optimización: select_related para evitar query adicional al comedor
        try:
            hitos_existente = (
                Hitos.objects.select_related("comedor")
                .filter(comedor=intervenciones.comedor)
                .first()
            )

            if not intervenciones.subintervencion_id:
                intervenciones.subintervencion = SubIntervencion.objects.create(
                    nombre=""
                )

            hitos_a_actualizar = HitosIntervenciones.objects.filter(
                intervencion=intervenciones.tipo_intervencion.nombre,
                subintervencion=intervenciones.subintervencion.nombre,
            )

            if hitos_existente:
                AcompanamientoService._actualizar_hitos(
                    hitos_existente, hitos_a_actualizar
                )
            else:
                nuevo_hito = Hitos.objects.create(comedor=intervenciones.comedor)
                AcompanamientoService._actualizar_hitos(nuevo_hito, hitos_a_actualizar)
        except Exception:
            logger.exception(
                "Error en AcomanamientoService.crear_hitos",
                extra={"intervenciones": intervenciones},
            )
            raise

    @staticmethod
    def _actualizar_hitos(hitos_objeto, hitos_a_actualizar):
        """Actualizar las banderas de un objeto :class:`Hitos`.

        Args:
            hitos_objeto (Hitos): Instancia a modificar.
            hitos_a_actualizar (QuerySet): Hitos a marcar como cumplidos.

        Returns:
            None
        """
        try:
            for hito in hitos_a_actualizar:
                for field in Hitos._meta.fields:
                    if field.verbose_name == hito.hito:
                        setattr(hitos_objeto, field.name, True)
            hitos_objeto.save()
        except Exception:
            logger.exception(
                "Error en AcompanamientoService.crear_hitos",
                extra={
                    "hitos_objeto": hitos_objeto,
                    "hitos_a_actualizar": hitos_a_actualizar,
                },
            )
            raise

    @staticmethod
    def obtener_hitos(comedor):
        """Obtener los hitos correspondientes a un comedor.

        Args:
            comedor: Comedor para el cual se solicitan los hitos.

        Returns:
            Hitos | None
        """
        try:
            return (
                Hitos.objects.select_related("comedor").filter(comedor=comedor).first()
            )
        except Exception:
            logger.exception(
                f"Error en AcompanamientoService.obtener_hitos para comedor: {comedor.pk}"
            )
            raise

    @staticmethod
    def obtener_fechas_hitos(comedor):
        """Obtener las fechas de las intervenciones que completaron cada hito.

        Args:
            comedor: Comedor para el cual se solicitan las fechas de hitos.

        Returns:
            dict: Diccionario con las fechas de cada hito completado.
        """
        try:
            fechas_hitos = {}

            intervenciones = (
                Intervencion.objects.filter(comedor=comedor)
                .select_related("tipo_intervencion", "subintervencion")
                .order_by("fecha")
            )

            for intervencion in intervenciones:
                if not intervencion.tipo_intervencion:
                    continue

                subintervencion_nombre = ""
                if intervencion.subintervencion:
                    subintervencion_nombre = intervencion.subintervencion.nombre

                hitos_completados = HitosIntervenciones.objects.filter(
                    intervencion=intervencion.tipo_intervencion.nombre,
                    subintervencion=subintervencion_nombre,
                )

                for hito_mapping in hitos_completados:

                    for field in Hitos._meta.fields:
                        if field.verbose_name == hito_mapping.hito:
                            fechas_hitos[field.name] = intervencion.fecha
                            break

            return fechas_hitos
        except Exception:
            logger.exception(
                f"Error en AcompanamientoService.obtener_fechas_hitos para comedor: {comedor.pk}"
            )
            return {}

    @staticmethod
    def importar_datos_desde_admision(comedor):
        """Copiar información relevante desde la admisión vinculada.

        Args:
            comedor: Comedor cuya admisión será consultada.

        Returns:
            None
        """
        try:
            try:
                admision = Admision.objects.get(comedor=comedor)
            except Admision.DoesNotExist as exc:
                raise ValueError(
                    "No se encontró una admisión para este comedor."
                ) from exc

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
            with transaction.atomic():
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
        except Exception:
            logger.exception(
                f"Error en AcompanamientoService.importar_datos_desde_admision para comedor: {comedor.pk}",
            )
            raise

    @staticmethod
    def obtener_datos_admision(comedor):
        """Obtener todos los datos relacionados con la admisión de un comedor.

        Args:
            comedor: Comedor del cual obtener los datos de admisión.

        Returns:
            dict: Diccionario con datos de admisión, info relevante, anexo, etc.
        """
        try:
            admision = (
                Admision.objects.filter(comedor=comedor)
                .exclude(legales_num_if__isnull=True)
                .exclude(legales_num_if="")
                .order_by("-id")
                .first()
            )

            info_relevante = None
            anexo = None
            resolucion = None

            if admision:
                info_relevante = (
                    InformeTecnico.objects.filter(admision=admision)
                    .order_by("-id")
                    .first()
                )
                anexo = Anexo.objects.filter(admision=admision).first()
                comedor = Comedor.objects.filter(id=admision.comedor_id).first()

                doc_resolucion = (
                    DocumentosExpediente.objects.filter(
                        admision=admision, tipo="Disposición"
                    )
                    .order_by("-creado")
                    .first()
                )
                if doc_resolucion:
                    resolucion = doc_resolucion.value or doc_resolucion.nombre

            return {
                "admision": admision,
                "comedor": comedor,
                "info_relevante": info_relevante,
                "anexo": anexo,
                "numero_if": admision.legales_num_if if admision else None,
                "numero_disposicion": resolucion,
            }
        except Exception:
            logger.exception(
                f"Error en AcompanamientoService.obtener_datos_admision para comedor: {comedor.pk}",
            )
            raise

    @staticmethod
    def obtener_prestaciones_detalladas(anexo):
        """Procesar los datos del anexo para generar las prestaciones por día y totales.

        Args:
            anexo: Anexo con los datos de prestaciones.

        Returns:
            dict: Diccionario con prestaciones_por_dia, prestaciones_dias y dias_semana.
        """
        try:
            if not anexo:
                return {
                    "prestaciones_por_dia": [],
                    "prestaciones_dias": [],
                    "dias_semana": [],
                }

            dias = [
                "lunes",
                "martes",
                "miercoles",
                "jueves",
                "viernes",
                "sabado",
                "domingo",
            ]
            tipos_comida = [
                "desayuno",
                "almuerzo",
                "merienda",
                "cena",
            ]

            prestaciones_por_dia = []
            prestaciones_totales = []

            for tipo in tipos_comida:
                fila = {"tipo": tipo.capitalize()}
                total_semanal = 0

                for dia in dias:
                    campo_nombre = f"{tipo}_{dia}"
                    cantidad = getattr(anexo, campo_nombre, 0)
                    fila[dia] = cantidad
                    total_semanal += cantidad or 0

                prestaciones_por_dia.append(fila)
                prestaciones_totales.append(
                    {"tipo": tipo.capitalize(), "cantidad": total_semanal}
                )

            return {
                "prestaciones_por_dia": prestaciones_por_dia,
                "prestaciones_dias": prestaciones_totales,
                "dias_semana": [dia.capitalize() for dia in dias],
            }
        except Exception:
            logger.exception(
                f"Error en AcompanamientoService.ontener_prestaciones_detalladas para anexo: {anexo.pk}",
            )
            raise

    @staticmethod
    def obtener_comedores_acompanamiento(user, busqueda=None):
        """
        Obtiene un queryset de objetos Comedor que cumplen con los criterios de acompañamiento,
        filtrando según el usuario y una búsqueda opcional.

        - Si el usuario es superusuario o pertenece al grupo "Area Legales", obtiene todos los comedores
          con admisión en estado 2 y enviados a acompañamiento.
        - Si no, filtra los comedores donde el usuario es abogado o técnico asignado en la dupla.
        - Permite aplicar un filtro de búsqueda global sobre varios campos relacionados (nombre, provincia,
          tipo de comedor, dirección, referente, etc.).

        Args:
            user (User): Usuario autenticado que realiza la consulta.
            busqueda (str, optional): Texto de búsqueda global para filtrar los resultados. Por defecto es None.

        Returns:
            QuerySet: QuerySet de objetos Comedor filtrados según los criterios especificados.
        """
        try:

            user_groups = list(user.groups.values_list("name", flat=True))
            is_area_legales = "Area Legales" in user_groups
            is_dupla = (
                "Tecnico Comedor" in user_groups or "Abogado Dupla" in user_groups
            )

            # Subqueries para evitar JOINs 1:N y uso de distinct()
            admision_subq = Admision.objects.filter(
                comedor=OuterRef("pk"), enviado_acompaniamiento=True
            )
            dupla_abogado_subq = Dupla.objects.filter(
                comedor=OuterRef("pk"), abogado=user
            )
            dupla_tecnico_subq = Dupla.objects.filter(
                comedor=OuterRef("pk"), tecnico=user
            )

            qs = Comedor.objects.select_related(
                "referente", "tipocomedor", "provincia", "dupla__abogado"
            )

            if not user.is_superuser:
                if is_dupla:
                    qs = qs.filter(
                        Exists(dupla_abogado_subq) | Exists(dupla_tecnico_subq)
                    )
                if is_area_legales:
                    qs = qs.filter(Exists(admision_subq))

            if busqueda:
                qs = qs.filter(
                    Q(nombre__icontains=busqueda)
                    | Q(provincia__nombre__icontains=busqueda)
                    | Q(tipocomedor__nombre__icontains=busqueda)
                    | Q(calle__icontains=busqueda)
                    | Q(numero__icontains=busqueda)
                    | Q(referente__nombre__icontains=busqueda)
                    | Q(referente__apellido__icontains=busqueda)
                    | Q(referente__celular__icontains=busqueda)
                )

            return qs
        except Exception:
            logger.exception(
                f"Error en AcompanamientoService.obtener_comedores_acompanamiento para user: {user.pk}",
            )
            raise

    @staticmethod
    def verificar_permisos_tecnico_comedor(user):
        """Verificar si el usuario tiene permisos de técnico de comedor.

        Args:
            user: Usuario a verificar.

        Returns:
            bool: True si tiene permisos, False en caso contrario.
        """
        try:
            return (
                user.is_superuser or user.groups.filter(name="Tecnico Comedor").exists()
            )
        except Exception:
            logger.exception(
                f"Error en Acompanamiento.verificar_permisos_tecnico_comedor para user: {user.pk}",
            )
            raise
