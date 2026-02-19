# Documentación SISOC

## Mapa de documentos
### 1. Contexto y panorama
- `docs/panorama.md`: visión general del sistema, su alcance y casos de uso principales.
- `docs/dominio.md`: modelo del dominio central y relaciones clave entre entidades.
- `docs/arquitectura.md`: resumen de la arquitectura técnica (apps, servicios, dependencias).
- `docs/documentacion_base_datos_celiaquia.md`: detalles específicos de la base de datos de Celiaquía.

### 2. Configuración y operación
- `docs/instalacion.md`: pasos para poner el entorno local en marcha, variables de entorno y dependencias de Docker.
- `docs/integraciones.md`: conexiones con servicios externos, caches y manejo de estáticos/media.
- `docs/operaciones.md`: tareas recurrentes, cron jobs y endpoints de health de producción.
- `docs/comandos_administracion.md`: utilidades de management (`manage.py`) disponibles para el equipo.

### 3. Guías funcionales y de desarrollo
- `docs/aplicaciones.md`: listado de apps de Django, rutas principales y responsabilidades generales.
- `docs/implementaciones/filtros_avanzados.md`: motor compartido de filtros, favoritos y cómo integrarlos en un nuevo listado.
- `docs/implementaciones/preferencias_columnas.md`: sistema de configuración de columnas, modal y helpers reutilizables.
- `docs/implementaciones/exportar_listados.md`: mixin CSV y helper JS para exportar datos con filtros/columnas activos.
- `docs/implementaciones/pwa_backend.md`: diseño e implementación actual de la API PWA (auth token, scope por comedor, endpoints y permisos).
- `docs/agentes.md`: guía rápida para asistentes automáticos y workflows de documentación.

### 4. Flujos y sincronizaciones
- `docs/flujos/comedor_sync.md`: cómo funciona la sincronización de comedores con servicios externos.
- `docs/flujos/relevamiento_sync.md`: flujo completo del sincronizador de relevamientos.
- `docs/flujos/consulta_renaper.md`: integración con RENAPER para la consulta de datos ciudadanos.
- `docs/flujos/cambio_programa_comedor.md`: procedimiento para cambiar programas asignados a comedores.

## Contexto mínimo
- Stack: Django + MySQL con despliegue vía Docker Compose. Evidencia: README.md:1-4 y docker-compose.yml:1-34.
- Variables de entorno documentadas en `.env.example` (incluye DB, GESTIONAR, RENAPER, puertos y dominio). Evidencia: .env.example:1-51.
- Servicios externos activos: GESTIONAR (sincronización de comedores/relevamientos) y RENAPER (consulta de ciudadanos). Evidencia: comedores/tasks.py:11-125, relevamientos/tasks.py:13-85, centrodefamilia/services/consulta_renaper.py:13-170.
