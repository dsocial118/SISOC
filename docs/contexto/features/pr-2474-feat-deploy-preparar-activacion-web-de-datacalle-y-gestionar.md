# Contexto de feature PR #2474 - feat(deploy): preparar activacion web de DataCalle y Gestionar

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2474
- Base: `development`
- Rama origen: `codex/pwa-web-activation`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Hay cambios en capa API/DRF y conviene revisar contratos de request/response.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2474.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `AGENT_REPO_MAP.md`
- `comedores/api_serializers.py`
- `comedores/api_views_territorial.py`
- `comedores/models.py`
- `docs/contexto/features/pr-2474-feat-deploy-preparar-activacion-web-de-datacalle-y-gestionar.md`
- `docs/operacion/deploy_pwas.md`
- `docs/operacion/nginx/sisoc-pwas.conf`
- `docs/registro/cambios/2026-09-08-activacion-pwa-web.md`
- `docs/registro/prs/PR-2474.md`
- `scripts/operacion/deploy_pwas.py`
- `scripts/operacion/pwas.json`
- `tests/test_admisiones_forms_unit.py`
- `tests/test_deploy_pwas.py`
- `tests/test_pwa_nginx.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2474-feat-deploy-preparar-activacion-web-de-datacalle-y-gestionar.md`
- `docs/operacion/deploy_pwas.md`
- `docs/operacion/nginx/sisoc-pwas.conf`
- `docs/registro/cambios/2026-09-08-activacion-pwa-web.md`
- `docs/registro/prs/PR-2474.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
