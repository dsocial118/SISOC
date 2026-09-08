# Contexto de feature PR #2479 - fix(deploy): conservar lectura del código para workers

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2479
- Base: `development`
- Rama origen: `codex/pwa-worker-permissions`
- Autor: `juanikitro`

## Contexto funcional

- Evitar que el despliegue PWA impida arrancar workers del backend por permisos de lectura.

## Arquitectura tocada

- El alcance incluye automatización o tooling de CI/CD.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: fix
- Área principal declarada: deploy
- Impacto usuario declarado: Mantener disponibles los procesos de importación, credenciales y mailing tras desplegar.
- Riesgos / rollback: Umask 022 limitada al helper de backend; secretos y estado PWA conservan permisos privados. Verificar todos los workers además del healthcheck HTTP.

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2479.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.github/workflows/deploy.yml`
- `AGENT_REPO_MAP.md`
- `docs/operacion/deploy_automatizado.md`
- `docs/registro/cambios/2026-09-08-permisos-checkout-deploy-pwa.md`
- `tests/test_deploy_workflow.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/operacion/deploy_automatizado.md`
- `docs/registro/cambios/2026-09-08-permisos-checkout-deploy-pwa.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
