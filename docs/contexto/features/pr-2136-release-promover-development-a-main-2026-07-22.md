# Contexto de feature PR #2136 - release: promover development a main (2026-07-22)

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2136
- Base: `main`
- Rama origen: `development`
- Autor: `juanikitro`

## Contexto funcional

- Promoción integral de development a main con saneamiento de migración ARCA.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Hay cambios en capa API/DRF y conviene revisar contratos de request/response.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: fix
- Área principal declarada: predeploy
- Impacto usuario declarado: Usuarios de CDI, comedores, admisiones y PWA reciben validaciones y documentos corregidos.
- Riesgos / rollback: Backup DB obligatorio; ARCA requiere restore para rollback.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: acompanamientos/templates/acompañamiento_detail.html, admisiones/templates/admisiones/admisiones_tecnicos_form.html, admisiones/templates/admisiones/informe_tecnico_complementario_detalle.html, centrodeinfancia/templates/centrodeinfancia/centrodeinfancia_form.html, centrodeinfancia/templates/centrodeinfancia/trabajador_form.html, comedores/templates/comedor/certificaciones_prestaciones_historial.html, comedores/templates/comedor/comedor_convenio_pnud_form.html, comedores/templates/comedor/comedor_detail.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2136.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `AGENTS.md`
- `AGENT_REPO_MAP.md`
- `acompanamientos/templates/acompañamiento_detail.html`
- `acompanamientos/views.py`
- `admisiones/services/admisiones_service/impl.py`
- `admisiones/services/informes_service/impl.py`
- `admisiones/templates/admisiones/admisiones_tecnicos_form.html`
- `admisiones/templates/admisiones/informe_tecnico_complementario_detalle.html`
- `admisiones/views/web_views.py`
- `centrodeinfancia/forms.py`
- `centrodeinfancia/migrations/0039_alter_trabajador_es_interprete_and_more.py`
- `centrodeinfancia/migrations/0040_trabajador_campos_verificados_renaper.py`
- `centrodeinfancia/migrations/0041_trabajador_fecha_actualizacion_and_more.py`
- `centrodeinfancia/models.py`
- `centrodeinfancia/templates/centrodeinfancia/centrodeinfancia_form.html`
- `centrodeinfancia/templates/centrodeinfancia/trabajador_form.html`
- `centrodeinfancia/tests/test_access_scope_centrodeinfancia.py`
- `centrodeinfancia/tests/test_automatic_user_provisioning.py`
- `centrodeinfancia/tests/test_centrodeinfancia_form.py`
- `centrodeinfancia/tests/test_trabajador_form.py`
- ... y 66 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/ia/MODULAR_BOUNDARIES.md`
- `docs/infra/ENVIRONMENT_DATABASES.md`
- `docs/infra/QA_INVENTORY.md`
- `docs/infra/QA_MIGRATION_NOTES.md`
- `docs/infra/QA_OPERATIONS.md`
- `docs/infra/QA_RISKS.md`
- `docs/infra/QA_ROLLBACK.md`
- `docs/plans/2026-07-13-qa-local-mysql-retirement-design.md`
- `docs/registro/cambios/2026-07-14-cdi-validaciones-alta.md`
- `docs/registro/cambios/2026-07-16-cdi-validaciones-trabajador.md`
- `docs/registro/cambios/2026-07-20-ajustes-pwa-convenios-rendiciones-documentos.md`
- `docs/registro/cambios/2026-07-20-fix-migracion-arca-por-convenio.md`
- `docs/registro/cambios/2026-07-20-issue-2113-informe-tecnico-complementario.md`
- `docs/registro/cambios/2026-07-21-issue-1901-seguimiento-certificaciones.md`
- `docs/registro/cambios/2026-07-21-retiro-stage2-mysql-local-qa.md`
- `docs/registro/cambios/2026-07-22-issue-2133-rendiciones-pwa.md`
- `docs/registro/decisiones/2026-07-21-modulos-nuevos-extraibles.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
