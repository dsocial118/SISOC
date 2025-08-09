# centrodefamilia/services/informe_cabal_reprocess.py
from typing import Optional, Dict, Any, Iterable
from django.db import transaction
from django.db.models import Q, Count
from django.utils import timezone

from centrodefamilia.models import Centro, CabalArchivo, InformeCabalRegistro


def _norm(s: str) -> str:
    """Normaliza valores para comparar: quita espacios/ceros a izquierda."""
    if s is None:
        return ""
    s = str(s).strip()
    # si tenés códigos con ceros a izquierda y querés preservarlos, quita el lstrip
    return s.lstrip("0") or "0"


def _centros_index() -> dict:
    """
    Devuelve un índice en memoria por código normalizado -> Centro.
    (Si tu match es por otra clave, cambiá aquí.)
    """
    idx = {}
    for c in Centro.objects.only("id", "codigo", "activo"):
        key = _norm(c.codigo)
        if key:
            idx[key] = c
    return idx


@transaction.atomic
def reprocesar_registros_rechazados(
    *,
    archivo_id: Optional[int] = None,
    centro_id: Optional[int] = None,
    only_pago_rechazado: bool = False,
    dry_run: bool = False,
    batch_size: int = 500,
) -> Dict[str, Any]:
    """
    Reprocesa SOLO registros rechazados por “no coincidencia de centro”.
    - Criterio base: centro IS NULL o no_coincidente=True
    - Si only_pago_rechazado=True, además exige motivo_rechazo != '0'
      (i.e. pago no aceptado). Por defecto es False (se reprocesa todo).

    Filtros:
      - archivo_id: limita a un archivo.
      - centro_id: limita a registros cuyo nro_comercio coincida con ese centro (útil para probar).

    Efectos:
      - Si encuentra match (nro_comercio == Centro.codigo normalizado),
        setea registro.centro, no_coincidente=False.
      - Recalcula total_validas / total_invalidas en CabalArchivo afectado.
      - dry_run=True: simula sin guardar cambios.

    Retorna métricas del proceso.
    """
    qs = InformeCabalRegistro.objects.select_for_update().filter(
        Q(centro__isnull=True) | Q(no_coincidente=True)
    )

    if only_pago_rechazado:
        qs = qs.exclude(motivo_rechazo="0")

    if archivo_id:
        qs = qs.filter(archivo_id=archivo_id)

    if centro_id:
        # Solo registros cuyo nro_comercio pueda coincidir con el centro dado
        try:
            c = Centro.objects.only("codigo").get(pk=centro_id)
            qs = qs.filter(nro_comercio__iexact=c.codigo)
        except Centro.DoesNotExist:
            return {
                "ok": False,
                "error": f"Centro {centro_id} no existe.",
                "actualizados": 0,
                "total_candidatos": 0,
            }

    total_candidatos = qs.count()
    if total_candidatos == 0:
        return {"ok": True, "msg": "No hay registros para reprocesar.", "actualizados": 0, "total_candidatos": 0}

    centros_idx = _centros_index()

    actualizados = 0
    archivos_afectados = set()

    # Procesado por tandas
    start = 0
    while True:
        regs = list(qs.order_by("id")[start : start + batch_size])
        if not regs:
            break
        start += batch_size

        for r in regs:
            key = _norm(r.nro_comercio)
            centro = centros_idx.get(key)
            if centro:
                # asignar
                r.centro = centro
                r.no_coincidente = False
                if not dry_run:
                    r.save(update_fields=["centro", "no_coincidente"])
                actualizados += 1
                archivos_afectados.add(r.archivo_id)

    # Recalcular totales por archivo
    if not dry_run and archivos_afectados:
        for aid in archivos_afectados:
            _recalcular_totales_archivo(aid)

    return {
        "ok": True,
        "actualizados": actualizados,
        "total_candidatos": total_candidatos,
        "archivos_afectados": list(archivos_afectados),
        "dry_run": dry_run,
        "timestamp": timezone.now().isoformat(),
    }


def _recalcular_totales_archivo(archivo_id: int) -> None:
    """
    Recalcula total_filas, total_validas (con centro), total_invalidas.
    """
    archivo = CabalArchivo.objects.get(pk=archivo_id)
    base = InformeCabalRegistro.objects.filter(archivo_id=archivo_id)
    total = base.count()
    validas = base.filter(centro__isnull=False).count()
    invalidas = total - validas

    archivo.total_filas = total
    archivo.total_validas = validas
    archivo.total_invalidas = invalidas
    archivo.save(update_fields=["total_filas", "total_validas", "total_invalidas"])
