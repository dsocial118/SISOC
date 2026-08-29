# Contexto de feature PR #2356 - chore(sync): integrar main en homologacion

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2356
- Base: `homologacion`
- Rama origen: `automation/sync-main-to-homologacion`
- Autor: `sisoc-release-automation[bot]`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Hay cambios en capa API/DRF y conviene revisar contratos de request/response.
- Se modifican templates, con posible impacto visual o de composición UI.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: centrodeinfancia/templates/centrodeinfancia/centrodeinfancia_form.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2356.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `CHANGELOG.md`
- `centrodeinfancia/forms.py`
- `centrodeinfancia/management/__init__.py`
- `centrodeinfancia/management/commands/__init__.py`
- `centrodeinfancia/management/commands/relevar_cdi_duplicados.py`
- `centrodeinfancia/templates/centrodeinfancia/centrodeinfancia_form.html`
- `centrodeinfancia/tests/test_centrodeinfancia_form.py`
- `centrodeinfancia/tests/test_relevar_cdi_duplicados_command.py`
- `docs/contexto/features/pr-2350-feat-cdi-prevenir-duplicados-por-referente.md`
- `docs/contexto/features/pr-2351-docs-postman-cubrir-la-api-publica-completa-de-vat.md`
- `docs/contexto/features/pr-2353-chore-release-promover-development-a-main-2026-08-26.md`
- `docs/contexto/features/pr-2354-docs-release-preparar-predeploy-development-main-2026-08-26.md`
- `docs/plans/2026-08-26-vat-postman-api-completa-design.md`
- `docs/registro/cambios/2026-08-20-reset-password-issue-2236.md`
- `docs/registro/cambios/2026-08-26-issue-2349-cdi-duplicados.md`
- `docs/registro/cambios/2026-08-26-vat-postman-api-completa.md`
- `docs/registro/prs/PR-2350.md`
- `docs/registro/prs/PR-2351.md`
- `docs/registro/prs/PR-2353.md`
- `docs/registro/prs/PR-2354.md`
- ... y 4 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2350-feat-cdi-prevenir-duplicados-por-referente.md`
- `docs/contexto/features/pr-2351-docs-postman-cubrir-la-api-publica-completa-de-vat.md`
- `docs/contexto/features/pr-2353-chore-release-promover-development-a-main-2026-08-26.md`
- `docs/contexto/features/pr-2354-docs-release-preparar-predeploy-development-main-2026-08-26.md`
- `docs/plans/2026-08-26-vat-postman-api-completa-design.md`
- `docs/registro/cambios/2026-08-20-reset-password-issue-2236.md`
- `docs/registro/cambios/2026-08-26-issue-2349-cdi-duplicados.md`
- `docs/registro/cambios/2026-08-26-vat-postman-api-completa.md`
- `docs/registro/prs/PR-2350.md`
- `docs/registro/prs/PR-2351.md`
- `docs/registro/prs/PR-2353.md`
- `docs/registro/prs/PR-2354.md`
- `docs/registro/releases/pending/2026-08-26-pr-2353.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
