# Contexto de feature PR #2210 - revert(centrodeinfancia): restaurar talla legacy como texto

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2210
- Base: `main`
- Rama origen: `codex/revert-cdi-talla-migration-20260730`
- Autor: `juanikitro`

## Contexto funcional

- Desbloquear el deploy de producción sin convertir ni modificar tallas históricas.

## Arquitectura tocada

- Existen cambios de persistencia o migraciones que requieren revisión de datos.
- El alcance incluye automatización o tooling de CI/CD.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: Corrección de migración y rollback funcional.
- Área principal declarada: Centro de Infancia y despliegue productivo.
- Impacto usuario declarado: El alta CDI vuelve a aceptar talla textual u omitida; no se alteran registros existentes.
- Riesgos / rollback: No migrar hacia atrás de 0043 sin backup y preflight de valores de talla.

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2210.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.github/workflows/deploy.yml`
- `centrodeinfancia/forms.py`
- `centrodeinfancia/migrations/0042_alter_nominacentroinfancia_talla.py`
- `centrodeinfancia/migrations/0043_revert_nominacentroinfancia_talla_to_text.py`
- `centrodeinfancia/models.py`
- `centrodeinfancia/tests/test_destinatario_form.py`
- `centrodeinfancia/tests/test_talla_migration.py`
- `docs/operacion/deploy_automatizado.md`
- `docs/registro/cambios/2026-07-30-reversion-segura-talla-cdi.md`
- `tests/test_deploy_workflow.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/operacion/deploy_automatizado.md`
- `docs/registro/cambios/2026-07-30-reversion-segura-talla-cdi.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
