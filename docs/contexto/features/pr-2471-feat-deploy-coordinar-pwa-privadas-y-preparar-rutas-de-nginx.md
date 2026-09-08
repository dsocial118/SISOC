# Contexto de feature PR #2471 - feat(deploy): coordinar PWA privadas y preparar rutas de Nginx

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2471
- Base: `development`
- Rama origen: `codex/pwa-deploy-integration`
- Autor: `juanikitro`

## Contexto funcional

- PWA satélites de SISOC.

## Arquitectura tocada

- El alcance incluye automatización o tooling de CI/CD.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: infraestructura y documentación.
- Área principal declarada: despliegue HML/PRD y Nginx.
- Impacto usuario declarado: sin cambios de rutas instalados en esta entrega.
- Riesgos / rollback: fallos parciales explícitos, recuperación de imágenes por app; sin rollback de migraciones. Conservar releases e imágenes y controlar espacio en disco.

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2471.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.github/workflows/deploy.yml`
- `.gitignore`
- `AGENT_REPO_MAP.md`
- `docs/contexto/features/pr-2471-feat-deploy-coordinar-pwa-privadas-y-preparar-rutas-de-nginx.md`
- `docs/operacion/deploy_automatizado.md`
- `docs/operacion/deploy_pwas.md`
- `docs/operacion/nginx/sisoc-produccion.conf`
- `docs/operacion/nginx/sisoc-pwas-preview.conf.example`
- `docs/operacion/nginx/sisoc-pwas.conf`
- `docs/registro/cambios/2026-09-08-coordinacion-pwa-privadas.md`
- `docs/registro/prs/PR-2471.md`
- `scripts/operacion/deploy_pwas.py`
- `scripts/operacion/deploy_refresh.sh`
- `scripts/operacion/pwas.json`
- `scripts/operacion/render_pwa_nginx.py`
- `tests/test_deploy_pwas.py`
- `tests/test_deploy_refresh_script.py`
- `tests/test_deploy_workflow.py`
- `tests/test_pwa_nginx.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2471-feat-deploy-coordinar-pwa-privadas-y-preparar-rutas-de-nginx.md`
- `docs/operacion/deploy_automatizado.md`
- `docs/operacion/deploy_pwas.md`
- `docs/operacion/nginx/sisoc-produccion.conf`
- `docs/operacion/nginx/sisoc-pwas-preview.conf.example`
- `docs/operacion/nginx/sisoc-pwas.conf`
- `docs/registro/cambios/2026-09-08-coordinacion-pwa-privadas.md`
- `docs/registro/prs/PR-2471.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
