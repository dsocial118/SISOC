# centrodefamilia/services/informe_cabal_reprocess.py
from collections import defaultdict
from typing import Dict, Any
from django.db import transaction
from django.db.models import Count
from centrodefamilia.models import Centro, InformeCabalRegistro, CabalArchivo
from django.db.models import F


class ReprocessError(Exception): ...

@transaction.atomic
def reprocesar_registros_rechazados_por_codigo(codigo: str, *, dry_run: bool = False) -> Dict[str, Any]:
    """
    Reprocesa todos los registros rechazados (no_coincidente=True o centro=None)
    cuyo nro_comercio == codigo. Setea centro, limpia no_coincidente y
    actualiza contadores en CabalArchivo.
    """
    codigo = (codigo or "").strip()
    if not codigo:
        raise ReprocessError("Código de centro vacío")

    try:
        centro = Centro.objects.only("id").get(codigo=codigo)
    except Centro.DoesNotExist:
        raise ReprocessError(f"Código '{codigo}' no encontrado")

    # Seleccionamos SOLO rechazados de ese código
    qs = (InformeCabalRegistro.objects
          .select_for_update()
          .filter(nro_comercio=codigo)
          .filter(no_coincidente=True)  # la regla de negocio base
          )

    procesados = qs.count()
    if procesados == 0:
        return {"procesados": 0, "impactados": 0, "detalles": [], "por_archivo": {}}

    # Guardamos agrupación por archivo para después actualizar contadores
    # (lo hacemos ANTES del update masivo)
    por_archivo_ids = list(qs.values_list("archivo_id", flat=True))
    conteo_por_archivo = (qs.values("archivo_id")
                            .annotate(cnt=Count("id")))
    cnt_map = {row["archivo_id"]: row["cnt"] for row in conteo_por_archivo}

    # Impacto: setear centro y no_coincidente=False en un solo UPDATE
    impactados = (qs.update(centro=centro, no_coincidente=False))

    # Actualizar contadores de CabalArchivo (validas/invalidas) por archivo
    # total_validas += cnt, total_invalidas -= cnt
    # Lo hacemos por lotes para mantener claridad (volúmenes razonables)
    for archivo_id, cnt in cnt_map.items():
        CabalArchivo.objects.filter(id=archivo_id).update(
            total_validas = F("total_validas") + cnt,
            total_invalidas = F("total_invalidas") - cnt,
        )

    if dry_run:
        transaction.set_rollback(True)

    # Optional: devolver desglose por archivo para que puedas auditar
    return {
        "procesados": procesados,
        "impactados": impactados,
        "detalles": [f"centro_id={centro.id}, codigo={codigo}"],
        "por_archivo": cnt_map,  # {archivo_id: cantidad_impactada}
    }
