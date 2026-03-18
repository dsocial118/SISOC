# Documentación SISOC

## Mapa de documentos
### 1. Contexto y arquitectura
- `docs/contexto/panorama.md`: visión general del sistema, su alcance y casos de uso principales.
- `docs/contexto/dominio.md`: modelo del dominio central y relaciones clave entre entidades.
- `docs/contexto/arquitectura.md`: resumen de la arquitectura técnica (apps, servicios, dependencias).
- `docs/contexto/aplicaciones.md`: inventario y notas por aplicaciones del sistema.
- `docs/contexto/features/`: contexto incremental generado por PR para continuidad entre agentes y revisión.
- `docs/contexto/documentacion_base_datos_celiaquia.md`: detalles específicos de la base de datos de Celiaquía.

### 2. Configuración y operación
- `docs/operacion/instalacion.md`: pasos para poner el entorno local en marcha, variables de entorno y dependencias de Docker.
- `docs/operacion/integraciones.md`: conexiones con servicios externos, caches y manejo de estáticos/media.
- `docs/operacion/operaciones.md`: tareas recurrentes, cron jobs y endpoints de health de producción.
- `docs/operacion/infraestructura.md`: inventario de infraestructura operativo (entornos, arquitectura, networking, deploy, observabilidad, seguridad y roadmap infra).
- `docs/operacion/comandos_administracion.md`: utilidades de management (`manage.py`) disponibles para el equipo.

### 3. Seguridad
- `docs/seguridad/security_baseline.md`: baseline de seguridad general del proyecto.
- `docs/seguridad/security_baseline_pwa.md`: baseline de seguridad para capacidades PWA.

### 4. Guías funcionales e implementaciones
- `docs/implementaciones/csp.md`: configuración y uso de CSP (nonce en templates, modo report-only, checklist de validación).
- `docs/implementaciones/sentry.md`: implementación de Sentry (activación por entorno, variables, logging y validación).
- `docs/implementaciones/audittrail_mvp_fase1.md`: release notes y guía operativa de Fase 1 del MVP de auditoría (deploy/rollback, soporte, riesgos y métricas).
- `docs/implementaciones/audittrail_fase2.md`: metadata persistida (`AuditEntryMeta`), contexto de auditoría para procesos y guía de deploy/rollback de Fase 2.
- `docs/implementaciones/exportar_listados.md`: detalle del flujo de exportación de listados.
- `docs/implementaciones/filtros_avanzados.md`: comportamiento y consideraciones de filtros avanzados.
- `docs/implementaciones/preferencias_columnas.md`: preferencias de columnas en listados.
- `docs/implementaciones/pwa_backend.md`: implementación backend de funcionalidades PWA.
- `docs/implementaciones/usuarios_perfil_iam.md`: implementación de Usuarios/Perfil + IAM por permisos Django y guía para extender nuevas features.

### 5. Flujos y sincronizaciones
- `docs/flujos/comedor_sync.md`: cómo funciona la sincronización de comedores con servicios externos.
- `docs/flujos/relevamiento_sync.md`: flujo completo del sincronizador de relevamientos.
- `docs/flujos/consulta_renaper.md`: integración con RENAPER para la consulta de datos ciudadanos.
- `docs/flujos/cambio_programa_comedor.md`: procedimiento para cambiar programas asignados a comedores.

### 6. IA, planes y registro spec-as-source
- `docs/agentes/guia.md`: guía rápida para asistentes automáticos y flujo de documentación.
- `docs/ia/`: guías especializadas para asistentes (arquitectura, testing, seguridad, etc.).
- `docs/plans/`: diseños y planes previos de trabajo.
- `docs/registro/README.md`: reglas para registrar cambios y decisiones importantes en `docs/`.
- `docs/registro/cambios/`: historial de cambios importantes.
- `docs/registro/decisiones/`: decisiones relevantes (ADR livianas).
- `docs/registro/prs/`: documentación automática por pull request.
- `docs/registro/releases/pending/`: release notes preliminares usadas para reconstruir `CHANGELOG.md` en PRs a `main`.

### 7. Testing y QA
- `docs/testing/usuarios_test.md`: usuarios de prueba y alcance de testing manual.

## Contexto mínimo
- Stack: Django + MySQL con despliegue vía Docker Compose. Evidencia: README.md:1-4 y docker-compose.yml:1-34.
- Variables de entorno documentadas en `.env.example` (incluye DB, GESTIONAR, RENAPER, puertos y dominio). Evidencia: .env.example:1-51.
- Servicios externos activos: GESTIONAR (sincronización de comedores/relevamientos) y RENAPER (consulta de ciudadanos). Evidencia: comedores/tasks.py:11-125, relevamientos/tasks.py:13-85, centrodefamilia/services/consulta_renaper.py:13-170.
