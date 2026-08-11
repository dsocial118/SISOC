# Contexto de feature PR #2271 - refactor: enforce domain boundaries for phase 3

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2271
- Base: `development`
- Rama origen: `codex/issue-2244-2248-boundaries`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2271.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.importlinter`
- `AGENT_REPO_MAP.md`
- `VAT/global_urls.py`
- `audittrail/api.py`
- `audittrail/signals.py`
- `centrodefamilia/api.py`
- `centrodefamilia/tests/test_centrodefamilia_public_api.py`
- `centrodeinfancia/apps.py`
- `centrodeinfancia/forms.py`
- `centrodeinfancia/signals.py`
- `centrodeinfancia/tests/test_audit_signals.py`
- `centrodeinfancia/views.py`
- `ciudadanos/api.py`
- `config/urls_preview.py`
- `dashboard/views.py`
- `docs/registro/decisiones/2026-08-11-boundaries-fase-3.md`
- `intervenciones/api.py`
- `intervenciones/tests/test_intervenciones_public_api.py`
- `tests/test_ciudadanos_renaper_api_unit.py`
- `ver_para_ser_libre/tests/test_boundary_api.py`
- ... y 2 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/decisiones/2026-08-11-boundaries-fase-3.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
