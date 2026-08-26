from collections import defaultdict

from django.core.management.base import BaseCommand

from centrodeinfancia.models import CentroDeInfancia, normalizar_cuit


def _enmascarar_identificador(value):
    if len(value) <= 4:
        return value
    return f"{'*' * (len(value) - 4)}{value[-4:]}"


class Command(BaseCommand):
    help = (
        "Lista CDI activos duplicados por provincia, CUIT del organismo y CUIL "
        "del referente. No modifica registros."
    )

    def handle(self, *args, **options):
        grupos = defaultdict(list)
        centros = CentroDeInfancia.objects.select_related("provincia").iterator()

        for centro in centros:
            cuit = normalizar_cuit(centro.cuit_organizacion_gestiona)
            cuil = normalizar_cuit(centro.cuil_referente)
            if not centro.provincia_id or not cuit or not cuil:
                continue
            grupos[(centro.provincia_id, cuit, cuil)].append(centro)

        duplicados = [
            (clave, centros_grupo)
            for clave, centros_grupo in grupos.items()
            if len(centros_grupo) > 1
        ]
        duplicados.sort(key=lambda item: item[0])

        if not duplicados:
            self.stdout.write("No se encontraron CDI duplicados.")
            return

        for (_provincia_id, cuit, cuil), centros_grupo in duplicados:
            provincia = centros_grupo[0].provincia.nombre
            detalle_centros = ", ".join(
                f"{centro.pk} | {centro.nombre}"
                for centro in sorted(centros_grupo, key=lambda centro: centro.pk)
            )
            self.stdout.write(
                f"Provincia: {provincia} | CUIT: {_enmascarar_identificador(cuit)} "
                f"| CUIL referente: {_enmascarar_identificador(cuil)} "
                f"| {len(centros_grupo)} CDI(s): {detalle_centros}"
            )

        self.stdout.write(
            self.style.WARNING(f"Grupos duplicados detectados: {len(duplicados)}.")
        )
