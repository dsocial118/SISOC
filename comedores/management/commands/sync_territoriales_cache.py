"""
Management command para sincronizar cache de territoriales.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from comedores.models import Comedor, TerritorialSyncLog
from comedores.services.territorial_service import TerritorialService


class Command(BaseCommand):
    help = 'Sincroniza cache de territoriales con GESTIONAR'

    def add_arguments(self, parser):
        parser.add_argument(
            '--comedor-id',
            type=int,
            help='ID específico de comedor para sincronizar'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar sincronización aunque los datos estén actualizados'
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Limpiar logs de sincronización antiguos (>30 días)'
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Mostrar estadísticas del cache actual'
        )

    def handle(self, *args, **options):
        if options['stats']:
            self.mostrar_estadisticas()
            return
            
        if options['cleanup']:
            self.limpiar_logs_antiguos()
            return
            
        comedor_id = options.get('comedor_id')
        force = options.get('force', False)
        
        if comedor_id:
            self.sincronizar_comedor(comedor_id, force)
        else:
            self.sincronizar_por_lotes(force)

    def mostrar_estadisticas(self):
        """Muestra estadísticas del estado actual del cache."""
        stats = TerritorialService.obtener_estadisticas_cache()
        
        self.stdout.write(
            self.style.SUCCESS('=== Estadísticas Cache Territoriales ===')
        )
        self.stdout.write(f"Total territoriales activos: {stats.get('total_territoriales', 0)}")
        self.stdout.write(f"Territoriales desactualizados: {stats.get('desactualizados', 0)}")
        
        ultimo_sync = stats.get('ultimo_sync')
        if ultimo_sync:
            self.stdout.write(f"Último sync: {ultimo_sync}")
            self.stdout.write(f"Último sync exitoso: {'Sí' if stats.get('ultimo_sync_exitoso') else 'No'}")
        else:
            self.stdout.write("No hay registros de sincronización")
            
        cache_activo = stats.get('cache_django_activo')
        self.stdout.write(f"Cache Django activo: {'Sí' if cache_activo else 'No'}")

    def sincronizar_comedor(self, comedor_id, force):
        """Sincroniza territoriales para un comedor específico."""
        try:
            comedor = Comedor.objects.get(id=comedor_id)
            self.stdout.write(f"Sincronizando territoriales para comedor: {comedor.nombre}")
            
            resultado = TerritorialService.obtener_territoriales_para_comedor(
                comedor_id=comedor_id,
                forzar_sync=force
            )
            
            if resultado['territoriales']:
                count = len(resultado['territoriales'])
                fuente = resultado['fuente']
                desactualizados = resultado['desactualizados']
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Obtenidos {count} territoriales (fuente: {fuente}, "
                        f"desactualizados: {'Sí' if desactualizados else 'No'})"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING("⚠ No se obtuvieron territoriales")
                )
                
        except Comedor.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"✗ Comedor con ID {comedor_id} no existe")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Error sincronizando comedor {comedor_id}: {e}")
            )

    def sincronizar_por_lotes(self, force):
        """Sincroniza territoriales usando una muestra de comedores activos."""
        self.stdout.write("Iniciando sincronización por lotes...")
        
        # Obtener muestra de comedores activos
        comedores_muestra = Comedor.objects.filter(
            estado__in=['Activo', 'Asignado a Dupla Técnica', 'En proceso']
        ).order_by('?')[:5]  # Muestra aleatoria de 5 comedores
        
        if not comedores_muestra:
            self.stdout.write(
                self.style.WARNING("No hay comedores activos para sincronizar")
            )
            return
        
        exitos = 0
        errores = 0
        
        for comedor in comedores_muestra:
            try:
                self.stdout.write(f"Procesando comedor: {comedor.nombre}")
                
                resultado = TerritorialService.obtener_territoriales_para_comedor(
                    comedor_id=comedor.id,
                    forzar_sync=force
                )
                
                if resultado['fuente'] in ['gestionar_sync', 'db_local', 'cache_django']:
                    exitos += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ {len(resultado['territoriales'])} territoriales")
                    )
                    # Una sincronización exitosa es suficiente para actualizar el cache global
                    break
                else:
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠ Fuente: {resultado['fuente']}")
                    )
                    
            except Exception as e:
                errores += 1
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Error: {e}")
                )
        
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(f"Sincronización completada: {exitos} éxitos, {errores} errores")
        )

    def limpiar_logs_antiguos(self):
        """Limpia logs de sincronización antiguos."""
        fecha_limite = timezone.now() - timezone.timedelta(days=30)
        
        with transaction.atomic():
            logs_eliminados = TerritorialSyncLog.objects.filter(
                fecha__lt=fecha_limite
            ).delete()[0]
        
        self.stdout.write(
            self.style.SUCCESS(f"✓ Eliminados {logs_eliminados} logs antiguos")
        )