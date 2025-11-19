import logging
from typing import Dict, Iterable, List, Set

from django.db import transaction

from ciudadanos.models import GrupoFamiliar

logger = logging.getLogger("django")


class FamiliaService:
    """Servicios auxiliares para gestionar relaciones familiares."""

    @staticmethod
    def crear_relacion_responsable_hijo(
        responsable_id: int, hijo_id: int, usuario=None
    ) -> dict:
        """
        Crea (o actualiza) la relacion familiar entre un responsable y un hijo.
        Siempre asegura conviven=True y cuidador_principal=True para el responsable.
        """

        try:
            with transaction.atomic():
                relacion, creada = GrupoFamiliar.objects.get_or_create(
                    ciudadano_1_id=responsable_id,
                    ciudadano_2_id=hijo_id,
                    defaults={
                        "vinculo": GrupoFamiliar.RELACION_HIJO,
                        "conviven": True,
                        "cuidador_principal": True,
                    },
                )

                if not creada:
                    campos_actualizar: List[str] = []
                    if relacion.vinculo != GrupoFamiliar.RELACION_HIJO:
                        relacion.vinculo = GrupoFamiliar.RELACION_HIJO
                        campos_actualizar.append("vinculo")
                    if relacion.conviven is not True:
                        relacion.conviven = True
                        campos_actualizar.append("conviven")
                    if relacion.cuidador_principal is not True:
                        relacion.cuidador_principal = True
                        campos_actualizar.append("cuidador_principal")

                    if campos_actualizar:
                        relacion.save(update_fields=campos_actualizar)

                logger.info(
                    "Relacion familiar responsable=%s hijo=%s creada=%s",
                    responsable_id,
                    hijo_id,
                    creada,
                )

                return {
                    "success": True,
                    "relacion_creada": creada,
                    "relacion": relacion,
                }
        except Exception as exc:
            logger.error("Error creando relacion familiar: %s", exc)
            return {
                "success": False,
                "error": str(exc),
            }

    @staticmethod
    def obtener_hijos_a_cargo(responsable_id: int, expediente=None) -> List:
        """
        Devuelve la lista de hijos asociados a un responsable.
        Si se indica expediente, filtra los hijos a los que aplica dentro del mismo.
        """

        try:
            relaciones = (
                GrupoFamiliar.objects.filter(
                    ciudadano_1_id=responsable_id,
                    cuidador_principal=True,
                )
                .select_related("ciudadano_2")
                .order_by("ciudadano_2__apellido", "ciudadano_2__nombre")
            )

            hijos = [rel.ciudadano_2 for rel in relaciones]

            if expediente:
                legajo_ids = set(
                    expediente.expediente_ciudadanos.values_list(
                        "ciudadano_id", flat=True
                    )
                )
                hijos = [hijo for hijo in hijos if hijo.id in legajo_ids]

            return hijos
        except Exception as exc:
            logger.error("Error obteniendo hijos a cargo: %s", exc)
            return []

    @staticmethod
    def obtener_responsables(hijo_id: int) -> List:
        """Devuelve la lista de responsables de un hijo."""

        try:
            relaciones = (
                GrupoFamiliar.objects.filter(
                    ciudadano_2_id=hijo_id,
                    cuidador_principal=True,
                )
                .select_related("ciudadano_1")
                .order_by("ciudadano_1__apellido", "ciudadano_1__nombre")
            )
            return [rel.ciudadano_1 for rel in relaciones]
        except Exception as exc:
            logger.error("Error obteniendo responsables: %s", exc)
            return []

    @staticmethod
    def obtener_responsable_de_hijo(hijo_id: int):
        """Devuelve el ID del responsable principal de un hijo, o None si no tiene."""
        try:
            relacion = GrupoFamiliar.objects.filter(
                ciudadano_2_id=hijo_id,
                cuidador_principal=True,
            ).first()
            return relacion.ciudadano_1_id if relacion else None
        except Exception as exc:
            logger.error("Error obteniendo responsable de hijo: %s", exc)
            return None

    @staticmethod
    def es_responsable(ciudadano_id: int) -> bool:
        """Indica si el ciudadano tiene hijos a su cargo."""

        return GrupoFamiliar.objects.filter(
            ciudadano_1_id=ciudadano_id,
            cuidador_principal=True,
        ).exists()

    @staticmethod
    def obtener_ids_responsables(ciudadanos_ids: Iterable[int]) -> Set[int]:
        relaciones = GrupoFamiliar.objects.filter(
            ciudadano_1_id__in=ciudadanos_ids,
            cuidador_principal=True,
        ).values_list("ciudadano_1_id", flat=True)
        return set(relaciones)

    @staticmethod
    def obtener_responsables_por_hijo(
        ciudadanos_ids: Iterable[int],
    ) -> Dict[int, List]:
        """Devuelve un diccionario hijo_id -> lista de responsables."""

        if not ciudadanos_ids:
            return {}

        relaciones = (
            GrupoFamiliar.objects.filter(
                ciudadano_2_id__in=ciudadanos_ids,
                cuidador_principal=True,
            )
            .select_related("ciudadano_1")
            .order_by("ciudadano_1__apellido", "ciudadano_1__nombre")
        )

        responsables_por_hijo: Dict[int, List] = {}
        for relacion in relaciones:
            responsables_por_hijo.setdefault(relacion.ciudadano_2_id, []).append(
                relacion.ciudadano_1
            )
        return responsables_por_hijo

    @staticmethod
    def obtener_estructura_familiar_expediente(expediente) -> dict:
        """
        Devuelve la estructura familiar del expediente.
        Retorna responsables con sus hijos y los legajos sin responsable.
        """

        try:
            legajos = list(expediente.expediente_ciudadanos.select_related("ciudadano"))
            ciudadanos_ids = [legajo.ciudadano_id for legajo in legajos]

            responsables_ids = FamiliaService.obtener_ids_responsables(ciudadanos_ids)

            estructura = {
                "responsables": {},
                "hijos_sin_responsable": [],
            }

            legajos_por_ciudadano = {legajo.ciudadano_id: legajo for legajo in legajos}

            for legajo in legajos:
                ciudadano = legajo.ciudadano
                if ciudadano.id in responsables_ids:
                    hijos = FamiliaService.obtener_hijos_a_cargo(
                        ciudadano.id, expediente=expediente
                    )
                    estructura["responsables"][legajo] = {
                        "ciudadano": ciudadano,
                        "legajo": legajo,
                        "hijos": hijos,
                    }
                else:
                    responsables = FamiliaService.obtener_responsables(ciudadano.id)
                    responsables_en_expediente = [
                        resp
                        for resp in responsables
                        if resp.id in legajos_por_ciudadano
                    ]
                    if not responsables_en_expediente:
                        estructura["hijos_sin_responsable"].append(legajo)

            return estructura
        except Exception as exc:
            logger.error("Error obteniendo estructura familiar: %s", exc)
            return {
                "responsables": {},
                "hijos_sin_responsable": [],
                "error": str(exc),
            }
