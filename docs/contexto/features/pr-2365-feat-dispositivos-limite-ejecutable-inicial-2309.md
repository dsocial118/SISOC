# Contexto de feature PR #2365 - feat(dispositivos): límite ejecutable inicial (#2309)

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2365
- Base: `development`
- Rama origen: `codex/issue-2309-executable-boundary`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.
- El alcance incluye automatización o tooling de CI/CD.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: .github/scripts/dispositivos_build_gate.js, .github/scripts/dispositivos_build_gate.test.js, .github/scripts/dispositivos_deploy_preflight.js, .github/scripts/dispositivos_deploy_preflight.test.js, services/dispositivos/monolith_compat/app/templates/dispositivos_confirm_delete.html, services/dispositivos/monolith_compat/app/templates/dispositivos_detail.html, services/dispositivos/monolith_compat/app/templates/dispositivos_form.html, services/dispositivos/monolith_compat/app/templates/dispositivos_list.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2365.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.env.example`
- `.github/dispositivos-deploy-targets.json`
- `.github/scripts/dispositivos_build_gate.js`
- `.github/scripts/dispositivos_build_gate.test.js`
- `.github/scripts/dispositivos_deploy_preflight.js`
- `.github/scripts/dispositivos_deploy_preflight.test.js`
- `.github/workflows/dispositivos-build.yml`
- `.github/workflows/dispositivos-deploy-preflight.yml`
- `.github/workflows/dispositivos-deploy.yml`
- `.github/workflows/tests.yml`
- `.importlinter`
- `AGENT_REPO_MAP.md`
- `compose.dispositivos.deploy.yml`
- `compose.dispositivos.yml`
- `config/settings.py`
- `config/urls.py`
- `dispositivos/apps.py`
- `dispositivos/favorite_filters.py`
- `dispositivos/tests/test_dispositivo_form_assets.py`
- `docs/contexto/features/pr-2365-feat-dispositivos-limite-ejecutable-inicial-2309.md`
- ... y 71 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2365-feat-dispositivos-limite-ejecutable-inicial-2309.md`
- `docs/operacion/dispositivos_runtime_local.md`
- `docs/plans/2026-08-27-issue-2309-c1-monorepo-boundary-design.md`
- `docs/plans/2026-08-27-issue-2309-dispositivos-relocation-design.md`
- `docs/plans/2026-08-28-issue-2309-c2-runtime-design.md`
- `docs/plans/2026-08-28-issue-2309-c3-build-local-design.md`
- `docs/plans/2026-08-29-issue-2309-c3-2-required-gate-design.md`
- `docs/plans/2026-08-29-issue-2309-c3-3-deploy-preflight-design.md`
- `docs/plans/2026-08-29-issue-2309-c3-5-qa-isolated-deploy-design.md`
- `docs/registro/cambios/2026-08-28-dispositivos-c2-runtime-verificado.md`
- `docs/registro/cambios/2026-08-29-dispositivos-c3-2-gate-requerido.md`
- `docs/registro/cambios/2026-08-29-dispositivos-c3-3-preflight-declarativo.md`
- `docs/registro/cambios/2026-08-29-dispositivos-c3-4-qa-provisioning-preflight.md`
- `docs/registro/decisiones/2026-08-21-dispositivos-actor-boundary.md`
- `docs/registro/decisiones/2026-08-28-dispositivos-ownership-transitorio-etapa-a.md`
- `docs/registro/prs/PR-2365.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
