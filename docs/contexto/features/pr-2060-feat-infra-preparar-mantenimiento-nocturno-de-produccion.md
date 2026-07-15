# Contexto de feature PR #2060 - feat(infra): preparar mantenimiento nocturno de produccion

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2060
- Base: `main`
- Rama origen: `codex/prod-night-package`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- No se detectó un patrón arquitectónico dominante más allá del diff observado.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2060.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `docs/infra/PROD_CHANGE_PROPOSALS.md`
- `docs/infra/PROD_INVENTORY.md`
- `docs/infra/PROD_MIGRATION_CHECKLIST.md`
- `docs/infra/PROD_RISKS.md`
- `docs/plans/2026-07-14-produccion-ventana-nocturna-design.md`
- `docs/registro/cambios/2026-07-14-paquete-mantenimiento-produccion.md`
- `scripts/infra/backup_prod_configs.sh`
- `scripts/infra/cleanup_prod_disk.sh`
- `scripts/infra/healthcheck_prod.sh`
- `scripts/infra/install_prod_maintenance.sh`
- `scripts/infra/prepare_prod_mobile_checkout.sh`
- `scripts/infra/prod_night_preflight.sh`
- `scripts/infra/retire_prod_local_mysql_stage1.sh`
- `scripts/infra/rollback_prod_maintenance.sh`
- `scripts/infra/rollback_prod_mobile_checkout.sh`
- `scripts/infra/verify_prod_release.sh`
- `tests/test_prod_infra_scripts.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/infra/PROD_CHANGE_PROPOSALS.md`
- `docs/infra/PROD_INVENTORY.md`
- `docs/infra/PROD_MIGRATION_CHECKLIST.md`
- `docs/infra/PROD_RISKS.md`
- `docs/plans/2026-07-14-produccion-ventana-nocturna-design.md`
- `docs/registro/cambios/2026-07-14-paquete-mantenimiento-produccion.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
