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
- `docs/INFRA_README.md`: inventario de infraestructura operativo (entornos, arquitectura, networking, deploy, observabilidad, seguridad y roadmap infra).
- `docs/comandos_administracion.md`: utilidades de management (`manage.py`) disponibles para el equipo.

### 3. Guías funcionales y de desarrollo
- `docs/implementaciones/csp.md`: configuración y uso de CSP (nonce en templates, modo report-only, checklist de validación).
- `docs/implementaciones/audittrail_mvp_fase1.md`: release notes y guía operativa de Fase 1 del MVP de auditoría (deploy/rollback, soporte, riesgos y métricas).
- `docs/implementaciones/audittrail_fase2.md`: metadata persistida (`AuditEntryMeta`), contexto de auditoría para procesos y guía de deploy/rollback de Fase 2.
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
