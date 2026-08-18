from django.core.management.base import BaseCommand

from comedores.models import Comedor
from users.api import (
    obtener_ids_organizaciones_con_acceso_pwa,
    previsualizar_accesos_organizacion,
    sincronizar_accesos_organizacion,
)


class Command(BaseCommand):
    """Reconcilia los accesos PWA de los usuarios asociados a organizaciones.

    Sirve para el catch-up inicial: alcanza a los comedores que se crearon o
    cambiaron de organización antes de que existiera la propagación automática.
    Recalcula el alcance completo de cada organización, por lo que también
    repone espacios que un administrador hubiera deseleccionado manualmente.
    """

    help = (
        "Sincroniza los accesos PWA de usuarios asociados a organizaciones con "
        "los comedores que hoy pertenecen a cada organización."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--organizacion",
            type=int,
            action="append",
            dest="organizacion_ids",
            help="Limita la sincronización a una organización (repetible).",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Persiste los cambios. Sin este flag corre en modo dry-run.",
        )

    def handle(self, *args, **options):
        aplicar = options["apply"]
        organizacion_ids = self._resolver_organizaciones(options["organizacion_ids"])

        if not organizacion_ids:
            self.stdout.write(
                self.style.WARNING(
                    "No hay usuarios PWA asociados a organizaciones para sincronizar."
                )
            )
            return

        comedores_por_organizacion = self._comedores_por_organizacion(organizacion_ids)

        totales = self._sincronizar(
            organizacion_ids,
            comedores_por_organizacion,
            aplicar=aplicar,
        )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== Resumen ==="))
        self.stdout.write(f"Organizaciones procesadas: {len(organizacion_ids)}")
        self.stdout.write(f"Accesos dados de alta: {totales['altas']}")
        self.stdout.write(f"Accesos dados de baja: {totales['bajas']}")
        if not aplicar:
            self.stdout.write(
                self.style.WARNING(
                    "Modo dry-run: no se aplicaron cambios. Reejecutar con --apply."
                )
            )

    def _sincronizar(
        self, organizacion_ids, comedores_por_organizacion, *, aplicar
    ) -> dict:
        totales = {"altas": 0, "bajas": 0}
        for organizacion_id in organizacion_ids:
            comedor_ids = tuple(
                comedores_por_organizacion.get(organizacion_id, [])
            )
            if aplicar:
                resultado = sincronizar_accesos_organizacion(
                    organizacion_id=organizacion_id,
                    comedor_ids=comedor_ids,
                )
            else:
                resultado = previsualizar_accesos_organizacion(
                    organizacion_id=organizacion_id,
                    comedor_ids=comedor_ids,
                )
            totales["altas"] += resultado["altas"]
            totales["bajas"] += resultado["bajas"]
            if resultado["altas"] or resultado["bajas"]:
                self.stdout.write(
                    f"Organización {organizacion_id}: "
                    f"+{resultado['altas']} / -{resultado['bajas']} accesos "
                    f"sobre {len(comedor_ids)} comedores."
                )
        return totales

    def _resolver_organizaciones(self, organizacion_ids) -> list:
        requested_ids = (
            tuple(sorted(set(organizacion_ids))) if organizacion_ids else None
        )
        return list(obtener_ids_organizaciones_con_acceso_pwa(requested_ids))

    def _comedores_por_organizacion(self, organizacion_ids) -> dict:
        comedores_por_organizacion = {}
        for comedor_id, organizacion_id in Comedor.objects.filter(
            organizacion_id__in=organizacion_ids
        ).values_list("pk", "organizacion_id"):
            comedores_por_organizacion.setdefault(organizacion_id, []).append(
                comedor_id
            )
        return comedores_por_organizacion
