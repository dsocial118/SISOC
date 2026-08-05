# Contexto de feature PR #2155 - fix(ci): desbloquear auto-merge de sincronizaciones descendentes

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2155
- Base: `development`
- Rama origen: `codex/fix-downstream-sync-automerge`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- El alcance incluye automatización o tooling de CI/CD.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: .github/scripts/sync_main_downstream.js, .github/scripts/sync_main_downstream.test.js

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2155.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.github/scripts/sync_main_downstream.js`
- `.github/scripts/sync_main_downstream.test.js`
- `.github/workflows/sync-main-downstream.yml`
- `AGENT_REPO_MAP.md`
- `docs/operacion/deploy_automatizado.md`
- `docs/registro/cambios/2026-07-27-sincronizacion-descendente-con-checks-estrictos.md`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/operacion/deploy_automatizado.md`
- `docs/registro/cambios/2026-07-27-sincronizacion-descendente-con-checks-estrictos.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
