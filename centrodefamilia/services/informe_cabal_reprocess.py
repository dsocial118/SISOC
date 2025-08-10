# centrodefamilia/services/informe_cabal_reprocess.py
from __future__ import annotations
from typing import Dict, Any, List
from django.db import transaction
import logging

log = logging.getLogger(__name__)

class ReprocessError(Exception):
    pass

def reprocesar_registros_rechazados(centro_id: int, dry_run: bool = False) -> Dict[str, Any]:
    """
    Reprocesa los registros rechazados de un centro.
    Retorna un dict normalizado: {"procesados": int, "impactados": int, "detalles": [str, ...]}
    - procesados: cantidad de intentos de reproceso (registros iterados)
    - impactados: cantidad de registros que efectivamente modificaron/actualizaron algo
    - detalles: mensajes útiles (ids con error, etc.)
    """
    if not isinstance(centro_id, int) or centro_id <= 0:
        raise ReprocessError("centro_id inválido")

    procesados = 0
    impactados = 0
    detalles: List[str] = []

    # 1) Si querés que no queden cambios en dry_run, usamos atomic + rollback.
    with transaction.atomic():
        try:
            # TODO conecta con tu lógica real (lo que hoy corrés en consola):
            # from .mi_core_de_informe_cabal import obtener_rechazados, intentar_reprocesar
            # registros = obtener_rechazados(centro_id)
            # ---- Ejemplo genérico (reemplazar por tu implementación real) ----
            registros = _obtener_rechazados_stub(centro_id)  # TODO reemplazar
            for reg in registros:
                procesados += 1
                try:
                    # changed = intentar_reprocesar(reg)  # TODO reemplazar
                    changed = _intentar_reprocesar_stub(reg)  # TODO reemplazar
                    if changed:
                        impactados += 1
                except Exception as e:
                    log.exception("Error reprocesando registro %s", getattr(reg, "id", reg))
                    detalles.append(f"error en {getattr(reg, 'id', reg)}: {e}")

        except Exception as e:
            # si algo crítico falla arriba, lo reflejamos y dejamos rollback implícito por la excepción si sube
            raise ReprocessError(str(e)) from e
        finally:
            if dry_run:
                # anulamos cualquier cambio hecho dentro del bloque
                transaction.set_rollback(True)

    return {"procesados": procesados, "impactados": impactados, "detalles": detalles}


# ----------------- STUBS (borralos cuando conectes tu lógica real) -----------------
def _obtener_rechazados_stub(centro_id: int):
    # simulamos 3 registros rechazados
    return [{"id": 1}, {"id": 2}, {"id": 3}]

def _intentar_reprocesar_stub(reg) -> bool:
    # “procesa” y dice si impactó algo (ej: 2 de 3)
    return reg["id"] % 2 == 1
# -------------------------------------------------------------------------------
