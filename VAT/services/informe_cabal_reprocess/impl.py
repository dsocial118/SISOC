from typing import Dict, Any

from django.db import transaction
from django.db.models import Count, F

from VAT.models import Centro, InformeCabalRegistro, CabalArchivo


class ReprocessError(Exception): ...


@transaction.atomic
def reprocesar_registros_rechazados_por_codigo(
    codigo: str, *, dry_run: bool = False
) -> Dict[str, Any]:

    codigo = (codigo or "").strip()
    if not codigo:
        raise ReprocessError("Código de centro vacío")

    try:
        centro = Centro.objects.only("id").get(codigo=codigo)
    except Centro.DoesNotExist as exc:
        raise ReprocessError(f"Código '{codigo}' no encontrado") from exc

    qs = InformeCabalRegistro.objects.select_for_update().filter(
        nro_comercio=codigo, no_coincidente=True
    )

    procesados = qs.count()
    if procesados == 0:
        return {"procesados": 0, "impactados": 0, "detalles": [], "por_archivo": {}}

    conteo_por_archivo = qs.values("archivo_id").annotate(cnt=Count("id"))
    cnt_map = {row["archivo_id"]: row["cnt"] for row in conteo_por_archivo}

    impactados = qs.update(centro=centro, no_coincidente=False)

    for archivo_id, cnt in cnt_map.items():
        CabalArchivo.objects.filter(id=archivo_id).update(
            total_validas=F("total_validas") + cnt,
            total_invalidas=F("total_invalidas") - cnt,
        )

    if dry_run:
        transaction.set_rollback(True)

    return {
        "procesados": procesados,
        "impactados": impactados,
        "detalles": [f"centro_id={centro.id}, codigo={codigo}"],
        "por_archivo": cnt_map,
    }
