# Contexto de feature PR #2276 - refactor: sellar bounded context Comedores Core

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2276
- Base: `development`
- Rama origen: `codex/issue-2250-comedores-core`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2276.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.importlinter`
- `AGENT_REPO_MAP.md`
- `admisiones/apps.py`
- `admisiones/audit_signals.py`
- `admisiones/tests/test_admisiones_audit_signals.py`
- `audittrail/api.py`
- `audittrail/signals.py`
- `centrodeinfancia/tests/test_nomina_integridad.py`
- `centrodeinfancia/tests/test_trabajadores_views.py`
- `centrodeinfancia/views.py`
- `ciudadanos/api.py`
- `ciudadanos/services_importacion_masiva.py`
- `ciudadanos/views.py`
- `comedores/api.py`
- `comedores/apps.py`
- `comedores/audit_signals.py`
- `comedores/tests/test_comedores_audit_signals.py`
- `comunicados/forms.py`
- `comunicados/permissions.py`
- `comunicados/views.py`
- ... y 24 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2276-refactor-sellar-bounded-context-comedores-core.md`
- `docs/registro/decisiones/2026-08-12-bounded-context-comedores-core.md`
- `docs/registro/prs/PR-2276.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
