# Contexto de feature PR #2365 - feat(dispositivos): límite ejecutable inicial (#2309)

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2365
- Base: `development`
- Rama origen: `codex/issue-2309-executable-boundary`
- Autor: `juanikitro`

## Contexto funcional

- contratos v1 puros en application; el ORM, CRUD y adaptadores legacy permanecen en monolith_compat, sin cambio observable de CRUD.

## Arquitectura tocada

- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.
- El alcance incluye automatización o tooling de CI/CD.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: boundary ejecutable, C1.3.
- Área principal declarada: Dispositivos.
- Impacto usuario declarado: No informado
- Riesgos / rollback: el acceso legacy a Core y Users queda acotado a monolith_compat; revertir este corte sólo restaura ubicación y jobs, sin cambios de datos.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: services/dispositivos/monolith_compat/app/templates/dispositivos_confirm_delete.html, services/dispositivos/monolith_compat/app/templates/dispositivos_detail.html, services/dispositivos/monolith_compat/app/templates/dispositivos_form.html, services/dispositivos/monolith_compat/app/templates/dispositivos_list.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2365.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.github/workflows/tests.yml`
- `.importlinter`
- `AGENT_REPO_MAP.md`
- `config/settings.py`
- `config/urls.py`
- `dispositivos/apps.py`
- `dispositivos/favorite_filters.py`
- `dispositivos/tests/test_dispositivo_form_assets.py`
- `docs/contexto/features/pr-2365-feat-dispositivos-limite-ejecutable-inicial-2309.md`
- `docs/plans/2026-08-27-issue-2309-c1-monorepo-boundary-design.md`
- `docs/plans/2026-08-27-issue-2309-dispositivos-relocation-design.md`
- `docs/registro/decisiones/2026-08-21-dispositivos-actor-boundary.md`
- `docs/registro/decisiones/2026-08-28-dispositivos-ownership-transitorio-etapa-a.md`
- `docs/registro/prs/PR-2365.md`
- `services/__init__.py`
- `services/dispositivos/__init__.py`
- `services/dispositivos/application/__init__.py`
- `services/dispositivos/application/contracts/__init__.py`
- `services/dispositivos/application/contracts/v1/__init__.py`
- `services/dispositivos/application/contracts/v1/catalog.py`
- ... y 41 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2365-feat-dispositivos-limite-ejecutable-inicial-2309.md`
- `docs/plans/2026-08-27-issue-2309-c1-monorepo-boundary-design.md`
- `docs/plans/2026-08-27-issue-2309-dispositivos-relocation-design.md`
- `docs/registro/decisiones/2026-08-21-dispositivos-actor-boundary.md`
- `docs/registro/decisiones/2026-08-28-dispositivos-ownership-transitorio-etapa-a.md`
- `docs/registro/prs/PR-2365.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
