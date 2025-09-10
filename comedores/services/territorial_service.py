"""
Servicio para gestionar cache de territoriales con GESTIONAR.
"""

import logging
import os
import requests
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from typing import List, Dict, Optional, Tuple

from comedores.models import TerritorialCache, TerritorialSyncLog, Comedor
from core.models import Provincia

logger = logging.getLogger(__name__)


class TerritorialService:
    """
    Servicio para gestionar cache de territoriales con estrategia de fallback.
    """

    CACHE_TIMEOUT = 3600  # 1 hora
    SYNC_TIMEOUT = 300  # 5 minutos para evitar syncs muy frecuentes

    @classmethod
    def _get_cache_key_provincia(cls, provincia_id: int) -> str:
        """Genera la clave de cache para una provincia específica."""
        return f"territoriales_provincia_{provincia_id}"

    @classmethod
    def obtener_territoriales_para_comedor(
        cls, comedor_id: int, forzar_sync: bool = False
    ) -> Dict:
        """
        Obtiene territoriales con estrategia de cache híbrido por provincia.
        UX mejorado: Mostrar cache mientras se hace fetch en background.

        Args:
            comedor_id: ID del comedor
            forzar_sync: Si True, fuerza sincronización con GESTIONAR

        Returns:
            Dict con 'territoriales' (lista), 'desactualizados' (bool), 'fuente' (str) y 'provincia_id' (int)
        """
        try:
            # 1. Obtener provincia del comedor
            comedor = Comedor.objects.select_related("provincia").get(id=comedor_id)
            provincia_id = comedor.provincia.id
            cache_key = cls._get_cache_key_provincia(provincia_id)

            # 2. SIEMPRE mostrar cache primero (UX instantáneo)
            if not forzar_sync:
                cache_data = cache.get(cache_key)
                if cache_data:
                    logger.info(
                        f"Territoriales obtenidos desde Django cache provincia {provincia_id}"
                    )
                    return {
                        "territoriales": cache_data,
                        "desactualizados": False,
                        "fuente": "cache_provincia",
                        "provincia_id": provincia_id,
                    }

            # 3. Obtener desde DB por provincia
            territoriales_db = cls._obtener_desde_db_por_provincia(provincia_id)
            if territoriales_db["territoriales"] and not forzar_sync:
                # Actualizar Django cache
                cache.set(
                    cache_key, territoriales_db["territoriales"], cls.CACHE_TIMEOUT
                )
                logger.info(
                    f"Territoriales obtenidos desde DB local provincia {provincia_id}"
                )
                return {
                    "territoriales": territoriales_db["territoriales"],
                    "desactualizados": territoriales_db["desactualizados"],
                    "fuente": "db_provincia",
                    "provincia_id": provincia_id,
                }

            api_key = os.getenv("GESTIONAR_API_KEY", "")
            api_url = os.getenv("GESTIONAR_API_CREAR_COMEDOR", "")

            gestionar_disponible = bool(
                api_key
                and api_url
                and api_url not in ["localhost:8001", "http://localhost:8001/", ""]
            )

            # 4. Fetch desde GESTIONAR (usando comedor_id como antes, pero guardando por provincia)
            if gestionar_disponible and (
                forzar_sync or cls._necesita_sincronizacion_provincia(provincia_id)
            ):
                sync_result = cls._sincronizar_con_gestionar_provincia(
                    comedor_id, provincia_id
                )
                if sync_result["exitoso"]:
                    territoriales_actualizados = cls._obtener_desde_db_por_provincia(
                        provincia_id
                    )
                    # Actualizar cache Django
                    cache.set(
                        cache_key,
                        territoriales_actualizados["territoriales"],
                        cls.CACHE_TIMEOUT,
                    )
                    return {
                        "territoriales": territoriales_actualizados["territoriales"],
                        "desactualizados": False,
                        "fuente": "gestionar_provincia_sync",
                        "provincia_id": provincia_id,
                    }

            # 5. Fallback a datos existentes si falla sync
            if territoriales_db["territoriales"]:
                mensaje = f"Usando territoriales desactualizados como fallback para provincia {provincia_id}"
                if not gestionar_disponible:
                    mensaje += " (GESTIONAR no disponible/configurado)"
                logger.warning(mensaje)
                return {
                    "territoriales": territoriales_db["territoriales"],
                    "desactualizados": True,
                    "fuente": "fallback_provincia",
                    "provincia_id": provincia_id,
                }

            # Sin datos disponibles y sin conexión a GESTIONAR
            logger.error(
                f"No se pudieron obtener territoriales para provincia {provincia_id}. GESTIONAR no disponible y sin cache local."
            )
            return {
                "territoriales": [],
                "desactualizados": True,
                "fuente": "sin_datos",
                "provincia_id": provincia_id,
            }

        except Comedor.DoesNotExist:
            logger.exception(f"Comedor {comedor_id} no encontrado")
            return {
                "territoriales": [],
                "desactualizados": True,
                "fuente": "comedor_no_encontrado",
            }
        except Exception as e:
            logger.exception(
                f"Error en obtener_territoriales_para_comedor: {e}", exc_info=True
            )
            return {"territoriales": [], "desactualizados": True, "fuente": "error"}

    @classmethod
    def _obtener_desde_db(cls) -> Dict:
        """Obtiene territoriales desde la base de datos local."""
        try:
            territoriales = TerritorialCache.objects.filter(activo=True)
            hay_desactualizados = any(t.esta_desactualizado for t in territoriales)

            return {
                "territoriales": [t.to_dict() for t in territoriales],
                "desactualizados": hay_desactualizados,
            }
        except Exception as e:
            logger.exception(f"Error obteniendo territoriales desde DB: {e}")
            return {"territoriales": [], "desactualizados": True}

    @classmethod
    def _obtener_desde_db_por_provincia(cls, provincia_id: int) -> Dict:
        """Obtiene territoriales por provincia desde la base de datos local."""
        try:
            territoriales = TerritorialCache.objects.filter(
                provincia_id=provincia_id, activo=True
            )
            hay_desactualizados = any(t.esta_desactualizado for t in territoriales)

            return {
                "territoriales": [t.to_dict() for t in territoriales],
                "desactualizados": hay_desactualizados,
            }
        except Exception as e:
            logger.exception(
                f"Error obteniendo territoriales provincia {provincia_id}: {e}"
            )
            return {"territoriales": [], "desactualizados": True}

    @classmethod
    def _necesita_sincronizacion(cls) -> bool:
        """Determina si es necesario sincronizar con GESTIONAR."""
        try:
            # Verificar si hay datos muy desactualizados (más de 1 hora)
            tiempo_limite = timezone.now() - timezone.timedelta(hours=1)
            territoriales_viejos = TerritorialCache.objects.filter(
                fecha_ultimo_sync__lt=tiempo_limite
            ).count()

            ultimo_sync = (
                TerritorialSyncLog.objects.filter(exitoso=True)
                .order_by("-fecha")
                .first()
            )

            if ultimo_sync:
                tiempo_min_entre_syncs = timezone.now() - timezone.timedelta(minutes=5)
                if ultimo_sync.fecha > tiempo_min_entre_syncs:
                    return False  # Sync muy reciente

            return territoriales_viejos > 0 or not ultimo_sync

        except Exception as e:
            logger.exception(f"Error verificando necesidad de sincronización: {e}")
            return False

    @classmethod
    def _necesita_sincronizacion_provincia(cls, provincia_id: int) -> bool:
        """Determina si es necesario sincronizar una provincia específica con GESTIONAR."""
        try:
            # Verificar si hay datos muy desactualizados para esta provincia (más de 1 hora)
            tiempo_limite = timezone.now() - timezone.timedelta(hours=1)
            territoriales_viejos = TerritorialCache.objects.filter(
                provincia_id=provincia_id, fecha_ultimo_sync__lt=tiempo_limite
            ).count()

            # Verificar último sync exitoso para esta provincia
            # Obtener IDs de comedores de la provincia para filtrar correctamente
            comedores_provincia = Comedor.objects.filter(
                provincia_id=provincia_id
            ).values_list("id", flat=True)
            ultimo_sync = (
                TerritorialSyncLog.objects.filter(
                    exitoso=True, comedor_id__in=comedores_provincia
                )
                .order_by("-fecha")
                .first()
            )

            if ultimo_sync:
                tiempo_min_entre_syncs = timezone.now() - timezone.timedelta(minutes=5)
                if ultimo_sync.fecha > tiempo_min_entre_syncs:
                    return False  # Sync muy reciente para esta provincia

            return territoriales_viejos > 0 or not ultimo_sync

        except Exception as e:
            logger.exception(
                f"Error verificando necesidad de sincronización provincia {provincia_id}: {e}"
            )
            return False

    @classmethod
    def _sincronizar_con_gestionar(cls, comedor_id: int) -> Dict:
        """
        Sincroniza territoriales con GESTIONAR (método legacy).

        Returns:
            Dict con 'exitoso' (bool) y 'mensaje' (str)
        """
        sync_log = TerritorialSyncLog(comedor_id=comedor_id)

        try:
            payload = {
                "Action": "Find",
                "Properties": {"Locale": "es-ES"},
                "Rows": [{"ComedorID": comedor_id}],
            }

            api_key = os.getenv("GESTIONAR_API_KEY", "")
            api_url = os.getenv("GESTIONAR_API_CREAR_COMEDOR", "")

            headers = {
                "applicationAccessKey": api_key,
                "Content-Type": "application/json",
            }

            if not api_url or not api_key:
                raise ValueError("Configuración de GESTIONAR incompleta")

            response = requests.post(api_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            raw_territoriales = (
                data[0].get("ListadoRelevadoresDisponibles", "") if data else ""
            )

            territoriales_data = cls._parse_territoriales_string(raw_territoriales)

            territoriales_sincronizados = cls._actualizar_cache_db(territoriales_data)

            sync_log.exitoso = True
            sync_log.territoriales_sincronizados = territoriales_sincronizados
            sync_log.save()

            logger.info(
                f"Sincronización exitosa: {territoriales_sincronizados} territoriales"
            )

            return {
                "exitoso": True,
                "mensaje": f"Sincronizados {territoriales_sincronizados} territoriales",
            }

        except Exception as e:
            error_msg = f"Error en sincronización con GESTIONAR: {e}"
            logger.exception(error_msg)

            sync_log.exitoso = False
            sync_log.error_mensaje = error_msg[:500]  # Truncar si es muy largo
            sync_log.save()

            return {"exitoso": False, "mensaje": error_msg}

    @classmethod
    def _sincronizar_con_gestionar_provincia(
        cls, comedor_id: int, provincia_id: int
    ) -> Dict:
        """
        Sincroniza territoriales usando comedor_id (API) pero guarda por provincia_id (Cache).

        Args:
            comedor_id: ID del comedor para la API de GESTIONAR
            provincia_id: ID de la provincia para el cache

        Returns:
            Dict con 'exitoso' (bool) y 'mensaje' (str)
        """
        sync_log = TerritorialSyncLog(comedor_id=comedor_id)

        try:
            # API call igual que antes (usa comedor_id)
            payload = {
                "Action": "Find",
                "Properties": {"Locale": "es-ES"},
                "Rows": [{"ComedorID": comedor_id}],  # API sigue usando ComedorID
            }

            api_key = os.getenv("GESTIONAR_API_KEY", "")
            api_url = os.getenv("GESTIONAR_API_CREAR_COMEDOR", "")

            headers = {
                "applicationAccessKey": api_key,
                "Content-Type": "application/json",
            }

            if not api_url or not api_key:
                raise ValueError("Configuración de GESTIONAR incompleta")

            response = requests.post(api_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            raw_territoriales = (
                data[0].get("ListadoRelevadoresDisponibles", "") if data else ""
            )

            territoriales_data = cls._parse_territoriales_string(raw_territoriales)

            # Actualizar cache por provincia (no global)
            territoriales_sincronizados = cls._actualizar_cache_db_provincia(
                territoriales_data, provincia_id
            )

            # Invalidar Django cache de la provincia
            cache_key = cls._get_cache_key_provincia(provincia_id)
            cache.delete(cache_key)

            sync_log.exitoso = True
            sync_log.territoriales_sincronizados = territoriales_sincronizados
            sync_log.save()

            logger.info(
                f"Sincronización exitosa provincia {provincia_id}: {territoriales_sincronizados} territoriales"
            )

            return {
                "exitoso": True,
                "mensaje": f"Sincronizados {territoriales_sincronizados} territoriales para provincia {provincia_id}",
            }

        except Exception as e:
            error_msg = (
                f"Error en sincronización con GESTIONAR provincia {provincia_id}: {e}"
            )
            logger.exception(error_msg)

            sync_log.exitoso = False
            sync_log.error_mensaje = error_msg[:500]  # Truncar si es muy largo
            sync_log.save()

            return {"exitoso": False, "mensaje": error_msg}

    @classmethod
    def _parse_territoriales_string(cls, raw_string: str) -> List[Dict]:
        """
        Parsea el string de territoriales de GESTIONAR.

        Formato esperado: "uid1/nombre1, uid2/nombre2, ..."
        """
        if not raw_string:
            return []

        territoriales = []
        items = raw_string.split(",")

        for item in items:
            item = item.strip()
            if "/" in item:
                parts = item.split("/", 1)  # Split solo en el primer /
                if len(parts) == 2:
                    gestionar_uid = parts[0].strip()
                    nombre = parts[1].strip()
                    if gestionar_uid and nombre:
                        territoriales.append(
                            {"gestionar_uid": gestionar_uid, "nombre": nombre}
                        )

        return territoriales

    @classmethod
    def _actualizar_cache_db(cls, territoriales_data: List[Dict]) -> int:
        """Actualiza el cache en base de datos (método legacy)."""
        if not territoriales_data:
            return 0

        contador = 0
        uids_recibidos = set()

        for territorial_data in territoriales_data:
            gestionar_uid = territorial_data["gestionar_uid"]
            nombre = territorial_data["nombre"]
            uids_recibidos.add(gestionar_uid)

            # Nota: Este método legacy no maneja provincias específicas
            # Se mantiene para compatibilidad pero no se recomienda su uso
            contador += 1

        return contador

    @classmethod
    def _actualizar_cache_db_provincia(
        cls, territoriales_data: List[Dict], provincia_id: int
    ) -> int:
        """Actualiza cache DB por provincia (limpia y recrea)."""
        if not territoriales_data:
            return 0

        with transaction.atomic():
            TerritorialCache.objects.filter(provincia_id=provincia_id).delete()
            logger.info(
                f"Limpiados territoriales existentes para provincia {provincia_id}"
            )

            contador = 0
            for territorial_data in territoriales_data:
                TerritorialCache.objects.create(
                    gestionar_uid=territorial_data["gestionar_uid"],
                    nombre=territorial_data["nombre"],
                    provincia_id=provincia_id,
                    activo=True,
                    fecha_ultimo_sync=timezone.now(),
                )
                contador += 1

            logger.info(
                f"Creados {contador} territoriales para provincia {provincia_id}"
            )
            return contador

    @classmethod
    def obtener_estadisticas_cache(cls) -> Dict:
        """Obtiene estadísticas del estado del cache."""
        try:
            total_territoriales = TerritorialCache.objects.filter(activo=True).count()
            desactualizados = TerritorialCache.objects.filter(
                activo=True,
                fecha_ultimo_sync__lt=timezone.now() - timezone.timedelta(hours=1),
            ).count()

            ultimo_sync = TerritorialSyncLog.objects.order_by("-fecha").first()

            return {
                "total_territoriales": total_territoriales,
                "desactualizados": desactualizados,
                "ultimo_sync": ultimo_sync.fecha if ultimo_sync else None,
                "ultimo_sync_exitoso": ultimo_sync.exitoso if ultimo_sync else None,
                "cache_django_activo": any(
                    cache.get(cls._get_cache_key_provincia(p.id)) is not None
                    for p in Provincia.objects.all()
                ),
            }

        except Exception as e:
            logger.exception(f"Error obteniendo estadísticas: {e}")
            return {}

    @classmethod
    def limpiar_cache_completo(cls):
        """Limpia todo el cache de territoriales."""
        try:
            # Limpiar Django cache para todas las provincias
            provincias = Provincia.objects.all()
            cache_keys_limpiadas = 0
            for provincia in provincias:
                cache_key = cls._get_cache_key_provincia(provincia.id)
                if cache.delete(cache_key):
                    cache_keys_limpiadas += 1

            # Limpiar DB cache (marcar como inactivo)
            TerritorialCache.objects.update(activo=False)

            logger.info(
                f"Cache de territoriales limpiado completamente: {cache_keys_limpiadas} claves de cache eliminadas"
            )

        except Exception as e:
            logger.exception(f"Error limpiando cache: {e}")
