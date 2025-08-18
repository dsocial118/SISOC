"""
Servicio para gestionar cache de territoriales con GESTIONAR.
"""
import logging
import os
import requests
from django.core.cache import cache
from django.utils import timezone
from typing import List, Dict, Optional, Tuple

from comedores.models import TerritorialCache, TerritorialSyncLog

logger = logging.getLogger(__name__)


class TerritorialService:
    """
    Servicio para gestionar cache de territoriales con estrategia de fallback.
    """
    
    CACHE_KEY_TERRITORIALES = 'territoriales_list'
    CACHE_TIMEOUT = 3600  # 1 hora
    SYNC_TIMEOUT = 300  # 5 minutos para evitar syncs muy frecuentes
    
    @classmethod
    def obtener_territoriales_para_comedor(cls, comedor_id: int, forzar_sync: bool = False) -> Dict:
        """
        Obtiene territoriales con estrategia de cache híbrido.
        
        Args:
            comedor_id: ID del comedor
            forzar_sync: Si True, fuerza sincronización con GESTIONAR
            
        Returns:
            Dict con 'territoriales' (lista) y 'desactualizados' (bool)
        """
        try:
            # 1. Intentar obtener de cache Django (más rápido)
            if not forzar_sync:
                territoriales_cache = cache.get(cls.CACHE_KEY_TERRITORIALES)
                if territoriales_cache:
                    logger.info("Territoriales obtenidos desde Django cache")
                    return {
                        'territoriales': territoriales_cache,
                        'desactualizados': False,
                        'fuente': 'cache_django'
                    }
            
            territoriales_db = cls._obtener_desde_db()
            if territoriales_db['territoriales'] and not forzar_sync:
                # Cachear en Django cache
                cache.set(cls.CACHE_KEY_TERRITORIALES, territoriales_db['territoriales'], cls.CACHE_TIMEOUT)
                logger.info("Territoriales obtenidos desde DB local")
                return {
                    'territoriales': territoriales_db['territoriales'],
                    'desactualizados': territoriales_db['desactualizados'],
                    'fuente': 'db_local'
                }
            
            api_key = os.getenv("GESTIONAR_API_KEY", "")
            api_url = os.getenv("GESTIONAR_API_CREAR_COMEDOR", "")
            
            gestionar_disponible = bool(api_key and api_url and 
                                      api_url not in ['localhost:8001', 'http://localhost:8001/', ''])
            
            if gestionar_disponible and (forzar_sync or cls._necesita_sincronizacion()):
                sync_result = cls._sincronizar_con_gestionar(comedor_id)
                if sync_result['exitoso']:
                    territoriales_actualizados = cls._obtener_desde_db()
                    # Actualizar cache Django
                    cache.set(cls.CACHE_KEY_TERRITORIALES, territoriales_actualizados['territoriales'], cls.CACHE_TIMEOUT)
                    return {
                        'territoriales': territoriales_actualizados['territoriales'],
                        'desactualizados': False,
                        'fuente': 'gestionar_sync'
                    }
            
            if territoriales_db['territoriales']:
                mensaje = "Usando territoriales desactualizados como fallback"
                if not gestionar_disponible:
                    mensaje += " (GESTIONAR no disponible/configurado)"
                logger.warning(mensaje)
                return {
                    'territoriales': territoriales_db['territoriales'],
                    'desactualizados': True,
                    'fuente': 'fallback_desactualizado'
                }
            
            if not gestionar_disponible:
                logger.info("GESTIONAR no disponible, usando datos de ejemplo para desarrollo")
                cls._crear_datos_ejemplo()
                territoriales_ejemplo = cls._obtener_desde_db()
                if territoriales_ejemplo['territoriales']:
                    return {
                        'territoriales': territoriales_ejemplo['territoriales'],
                        'desactualizados': True,
                        'fuente': 'datos_ejemplo'
                    }
            
            logger.error("No se pudieron obtener territoriales de ninguna fuente")
            return {
                'territoriales': [],
                'desactualizados': True,
                'fuente': 'vacio'
            }
            
        except Exception as e:
            logger.error(f"Error en obtener_territoriales_para_comedor: {e}", exc_info=True)
            return {
                'territoriales': [],
                'desactualizados': True,
                'fuente': 'error'
            }
    
    @classmethod
    def _obtener_desde_db(cls) -> Dict:
        """Obtiene territoriales desde la base de datos local."""
        try:
            territoriales = TerritorialCache.objects.filter(activo=True)
            hay_desactualizados = any(t.esta_desactualizado for t in territoriales)
            
            return {
                'territoriales': [t.to_dict() for t in territoriales],
                'desactualizados': hay_desactualizados
            }
        except Exception as e:
            logger.error(f"Error obteniendo territoriales desde DB: {e}")
            return {'territoriales': [], 'desactualizados': True}
    
    @classmethod
    def _necesita_sincronizacion(cls) -> bool:
        """Determina si es necesario sincronizar con GESTIONAR."""
        try:
            # Verificar si hay datos muy desactualizados (más de 1 hora)
            tiempo_limite = timezone.now() - timezone.timedelta(hours=1)
            territoriales_viejos = TerritorialCache.objects.filter(
                fecha_ultimo_sync__lt=tiempo_limite
            ).count()
            
            ultimo_sync = TerritorialSyncLog.objects.filter(
                exitoso=True
            ).order_by('-fecha').first()
            
            if ultimo_sync:
                tiempo_min_entre_syncs = timezone.now() - timezone.timedelta(minutes=5)
                if ultimo_sync.fecha > tiempo_min_entre_syncs:
                    return False  # Sync muy reciente
            
            return territoriales_viejos > 0 or not ultimo_sync
            
        except Exception as e:
            logger.error(f"Error verificando necesidad de sincronización: {e}")
            return False
    
    @classmethod
    def _sincronizar_con_gestionar(cls, comedor_id: int) -> Dict:
        """
        Sincroniza territoriales con GESTIONAR.
        
        Returns:
            Dict con 'exitoso' (bool) y 'mensaje' (str)
        """
        sync_log = TerritorialSyncLog(comedor_id=comedor_id)
        
        try:
            payload = {
                "Action": "Find",
                "Properties": {"Locale": "es-ES"},
                "Rows": [{"ComedorID": comedor_id}]
            }
            
            api_key = os.getenv("GESTIONAR_API_KEY", "")
            api_url = os.getenv("GESTIONAR_API_CREAR_COMEDOR", "")
            
            headers = {
                "applicationAccessKey": api_key,
                "Content-Type": "application/json"
            }
            
            if not api_url or not api_key:
                raise ValueError("Configuración de GESTIONAR incompleta")
            
            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            raw_territoriales = data[0].get('ListadoRelevadoresDisponibles', '') if data else ''
            
            territoriales_data = cls._parse_territoriales_string(raw_territoriales)
            
            territoriales_sincronizados = cls._actualizar_cache_db(territoriales_data)
            
            cache.delete(cls.CACHE_KEY_TERRITORIALES)
            
            sync_log.exitoso = True
            sync_log.territoriales_sincronizados = territoriales_sincronizados
            sync_log.save()
            
            logger.info(f"Sincronización exitosa: {territoriales_sincronizados} territoriales")
            
            return {
                'exitoso': True,
                'mensaje': f'Sincronizados {territoriales_sincronizados} territoriales'
            }
            
        except Exception as e:
            error_msg = f"Error en sincronización con GESTIONAR: {e}"
            logger.error(error_msg, exc_info=True)
            
            sync_log.exitoso = False
            sync_log.error_mensaje = error_msg[:500]  # Truncar si es muy largo
            sync_log.save()
            
            return {
                'exitoso': False,
                'mensaje': error_msg
            }
    
    @classmethod
    def _parse_territoriales_string(cls, raw_string: str) -> List[Dict]:
        """
        Parsea el string de territoriales de GESTIONAR.
        
        Formato esperado: "uid1/nombre1, uid2/nombre2, ..."
        """
        if not raw_string:
            return []
        
        territoriales = []
        items = raw_string.split(',')
        
        for item in items:
            item = item.strip()
            if '/' in item:
                parts = item.split('/', 1)  # Split solo en el primer /
                if len(parts) == 2:
                    gestionar_uid = parts[0].strip()
                    nombre = parts[1].strip()
                    if gestionar_uid and nombre:
                        territoriales.append({
                            'gestionar_uid': gestionar_uid,
                            'nombre': nombre
                        })
        
        return territoriales
    
    @classmethod
    def _actualizar_cache_db(cls, territoriales_data: List[Dict]) -> int:
        """Actualiza el cache en base de datos."""
        if not territoriales_data:
            return 0
        
        contador = 0
        uids_recibidos = set()
        
        for territorial_data in territoriales_data:
            gestionar_uid = territorial_data['gestionar_uid']
            nombre = territorial_data['nombre']
            uids_recibidos.add(gestionar_uid)
            
            territorial, created = TerritorialCache.objects.update_or_create(
                gestionar_uid=gestionar_uid,
                defaults={
                    'nombre': nombre,
                    'activo': True,
                    'fecha_ultimo_sync': timezone.now()
                }
            )
            contador += 1
        
        # Desactivar territoriales que ya no están en GESTIONAR
        TerritorialCache.objects.exclude(
            gestionar_uid__in=uids_recibidos
        ).update(activo=False)
        
        return contador
    
    @classmethod
    def obtener_estadisticas_cache(cls) -> Dict:
        """Obtiene estadísticas del estado del cache."""
        try:
            total_territoriales = TerritorialCache.objects.filter(activo=True).count()
            desactualizados = TerritorialCache.objects.filter(
                activo=True,
                fecha_ultimo_sync__lt=timezone.now() - timezone.timedelta(hours=1)
            ).count()
            
            ultimo_sync = TerritorialSyncLog.objects.order_by('-fecha').first()
            
            return {
                'total_territoriales': total_territoriales,
                'desactualizados': desactualizados,
                'ultimo_sync': ultimo_sync.fecha if ultimo_sync else None,
                'ultimo_sync_exitoso': ultimo_sync.exitoso if ultimo_sync else None,
                'cache_django_activo': cache.get(cls.CACHE_KEY_TERRITORIALES) is not None
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    @classmethod
    def limpiar_cache_completo(cls):
        """Limpia todo el cache de territoriales."""
        try:
            # Limpiar Django cache
            cache.delete(cls.CACHE_KEY_TERRITORIALES)
            
            # Limpiar DB cache (marcar como inactivo)
            TerritorialCache.objects.update(activo=False)
            
            logger.info("Cache de territoriales limpiado completamente")
            
        except Exception as e:
            logger.error(f"Error limpiando cache: {e}")
    
    @classmethod
    def _crear_datos_ejemplo(cls):
        """Crea datos de ejemplo para desarrollo cuando GESTIONAR no está disponible."""
        try:
            # Datos de ejemplo para desarrollo
            territoriales_ejemplo = [
                {'gestionar_uid': 'DEV001', 'nombre': 'Territorial Norte (Desarrollo)'},
                {'gestionar_uid': 'DEV002', 'nombre': 'Territorial Sur (Desarrollo)'},
                {'gestionar_uid': 'DEV003', 'nombre': 'Territorial Este (Desarrollo)'},
                {'gestionar_uid': 'DEV004', 'nombre': 'Territorial Oeste (Desarrollo)'},
                {'gestionar_uid': 'DEV005', 'nombre': 'Territorial Centro (Desarrollo)'},
            ]
            
            # Solo crear si no existen datos
            if TerritorialCache.objects.count() == 0:
                for territorial_data in territoriales_ejemplo:
                    TerritorialCache.objects.create(
                        gestionar_uid=territorial_data['gestionar_uid'],
                        nombre=territorial_data['nombre'],
                        activo=True,
                        fecha_ultimo_sync=timezone.now()
                    )
                logger.info(f"Creados {len(territoriales_ejemplo)} territoriales de ejemplo")
                
        except Exception as e:
            logger.error(f"Error creando datos de ejemplo: {e}")