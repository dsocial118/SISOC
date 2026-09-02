# Contexto de feature PR #2418 - chore(sync): integrar main en homologacion

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2418
- Base: `homologacion`
- Rama origen: `automation/sync-main-to-homologacion`
- Autor: `sisoc-release-automation[bot]`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2418.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `AGENT_REPO_MAP.md`
- `CHANGELOG.md`
- `centrodeinfancia/services_nomina_ninos_pdf.py`
- `centrodeinfancia/tests/test_nomina_ninos_pdf.py`
- `core/integrations/renaper.py`
- `core/management/commands/audit_utf8_mojibake.py`
- `core/management/commands/repair_utf8_mojibake.py`
- `core/services/text_encoding.py`
- `docs/contexto/features/pr-2415-fix-reparar-mojibake-en-datos-y-renaper.md`
- `docs/contexto/features/pr-2418-chore-sync-integrar-main-en-homologacion.md`
- `docs/contexto/features/pr-2421-fix-encoding-reparar-mojibake-capitalizado-historico.md`
- `docs/plans/2026-09-01-reparacion-mojibake-capitalizado-design.md`
- `docs/plans/2026-09-01-reparacion-mojibake-datos-design.md`
- `docs/registro/cambios/2026-09-01-reparacion-mojibake-capitalizado.md`
- `docs/registro/cambios/2026-09-01-reparacion-mojibake-datos.md`
- `docs/registro/prs/PR-2415.md`
- `docs/registro/prs/PR-2418.md`
- `docs/registro/prs/PR-2421.md`
- `docs/registro/releases/pending/2026-09-02-pr-2415.md`
- `docs/registro/releases/pending/2026-09-02-pr-2421.md`
- ... y 3 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2415-fix-reparar-mojibake-en-datos-y-renaper.md`
- `docs/contexto/features/pr-2418-chore-sync-integrar-main-en-homologacion.md`
- `docs/contexto/features/pr-2421-fix-encoding-reparar-mojibake-capitalizado-historico.md`
- `docs/plans/2026-09-01-reparacion-mojibake-capitalizado-design.md`
- `docs/plans/2026-09-01-reparacion-mojibake-datos-design.md`
- `docs/registro/cambios/2026-09-01-reparacion-mojibake-capitalizado.md`
- `docs/registro/cambios/2026-09-01-reparacion-mojibake-datos.md`
- `docs/registro/prs/PR-2415.md`
- `docs/registro/prs/PR-2418.md`
- `docs/registro/prs/PR-2421.md`
- `docs/registro/releases/pending/2026-09-02-pr-2415.md`
- `docs/registro/releases/pending/2026-09-02-pr-2421.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
