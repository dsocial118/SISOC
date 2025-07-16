from django.db.models import Q
from admisiones.models.admisiones import (
    Admision,
    InformeTecnico,
    DocumentosExpediente,
    Anexo,
)
from acompanamientos.models.hitos import Hitos, HitosIntervenciones
from acompanamientos.models.acompanamiento import InformacionRelevante
from core.models import Prestacion
from intervenciones.models.intervenciones import Intervencion, SubIntervencion
from comedores.models import Comedor


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
        hitos_existente = (
            Hitos.objects.select_related("comedor")
            .filter(comedor=intervenciones.comedor)
            .first()
        )

        if intervenciones.subintervencion is None:
            intervenciones.subintervencion = SubIntervencion()
            intervenciones.subintervencion.nombre = ""

        hitos_a_actualizar = HitosIntervenciones.objects.filter(
            intervencion=intervenciones.tipo_intervencion.nombre,
            subintervencion=intervenciones.subintervencion.nombre,
        )

        if hitos_existente:
            AcompanamientoService._actualizar_hitos(hitos_existente, hitos_a_actualizar)
        else:
            nuevo_hito = Hitos.objects.create(comedor=intervenciones.comedor)
            AcompanamientoService._actualizar_hitos(nuevo_hito, hitos_a_actualizar)

    @staticmethod
    def _actualizar_hitos(hitos_objeto, hitos_a_actualizar):
        """Actualizar las banderas de un objeto :class:`Hitos`.

        Args:
            hitos_objeto (Hitos): Instancia a modificar.
            hitos_a_actualizar (QuerySet): Hitos a marcar como cumplidos.

        Returns:
            None
        """
        for hito in hitos_a_actualizar:
            for field in Hitos._meta.fields:
                if field.verbose_name == hito.hito:
                    setattr(hitos_objeto, field.name, True)
        hitos_objeto.save()

    @staticmethod
    def obtener_hitos(comedor):
        """Obtener los hitos correspondientes a un comedor.

        Args:
            comedor: Comedor para el cual se solicitan los hitos.

        Returns:
            Hitos | None
        """
        return Hitos.objects.select_related("comedor").filter(comedor=comedor).first()

    @staticmethod
    def importar_datos_desde_admision(comedor):
        """Copiar información relevante desde la admisión vinculada.

        Args:
            comedor: Comedor cuya admisión será consultada.

        Returns:
            None
        """
        admision = Admision.objects.get(comedor=comedor)
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

    @staticmethod
    def obtener_datos_admision(comedor):
        """Obtener todos los datos relacionados con la admisión de un comedor.

        Args:
            comedor: Comedor del cual obtener los datos de admisión.

        Returns:
            dict: Diccionario con datos de admisión, info relevante, anexo, etc.
        """
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
                InformeTecnico.objects.filter(admision=admision).order_by("-id").first()
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

    @staticmethod
    def obtener_prestaciones_detalladas(anexo):
        """Procesar los datos del anexo para generar las prestaciones por día y totales.

        Args:
            anexo: Anexo con los datos de prestaciones.

        Returns:
            dict: Diccionario con prestaciones_por_dia, prestaciones_dias y dias_semana.
        """
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
        tipos_comida = ["desayuno", "almuerzo", "merienda", "cena"]

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

    @staticmethod
    def obtener_comedores_acompanamiento(user, busqueda=None):
        """Obtener comedores que tienen admisiones finalizadas y están en acompañamiento.

        Args:
            user: Usuario actual para aplicar filtros de permisos.
            busqueda: Término de búsqueda opcional.

        Returns:
            QuerySet: Comedores filtrados.
        """
        # Filtramos las admisiones con estado=2 (Finalizada)
        admisiones = Admision.objects.filter(estado=2, enviado_acompaniamiento=True)

        if (
            not user.is_superuser
            and not user.groups.filter(name="Area Legales").exists()
        ):
            admisiones = admisiones.filter(
                Q(comedor__dupla__abogado=user) | Q(comedor__dupla__tecnico=user)
            )

        comedor_ids = admisiones.values_list("comedor_id", flat=True).distinct()

        queryset = Comedor.objects.filter(id__in=comedor_ids).select_related(
            "referente", "tipocomedor", "provincia"
        )

        if busqueda:
            busqueda = busqueda.strip().lower()
            queryset = queryset.filter(
                Q(nombre__icontains=busqueda)
                | Q(provincia__nombre__icontains=busqueda)
                | Q(tipocomedor__nombre__icontains=busqueda)
                | Q(calle__icontains=busqueda)
                | Q(numero__icontains=busqueda)
                | Q(referente__nombre__icontains=busqueda)
                | Q(referente__apellido__icontains=busqueda)
                | Q(referente__celular__icontains=busqueda)
            )

        return queryset

    @staticmethod
    def verificar_permisos_tecnico_comedor(user):
        """Verificar si el usuario tiene permisos de técnico de comedor.

        Args:
            user: Usuario a verificar.

        Returns:
            bool: True si tiene permisos, False en caso contrario.
        """
        return user.is_superuser or user.groups.filter(name="Tecnico Comedor").exists()
