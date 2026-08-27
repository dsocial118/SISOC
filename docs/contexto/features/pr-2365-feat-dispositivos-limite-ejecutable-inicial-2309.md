# Contexto de feature PR #2365 - feat(dispositivos): límite ejecutable inicial (#2309)

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2365
- Base: `development`
- Rama origen: `codex/issue-2309-executable-boundary`
- Autor: `juanikitro`

## Contexto funcional

- el paquete canónico y sus vistas se reubicaron; el monolito sigue atendiendo el CRUD mediante adaptadores configurados.

## Arquitectura tocada

- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: boundary ejecutable, primer corte.
- Área principal declarada: Dispositivos.
- Impacto usuario declarado: se preservan rutas, permisos y alcance territorial.
- Riesgos / rollback: una adaptación incorrecta podría cambiar permisos, alcance o el registro de filtros; revertir este commit restaura el paquete en el monolito sin cambiar rutas, tablas, FKs ni escritor.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: services/dispositivos/dispositivos/templates/dispositivos_confirm_delete.html, services/dispositivos/dispositivos/templates/dispositivos_detail.html, services/dispositivos/dispositivos/templates/dispositivos_form.html, services/dispositivos/dispositivos/templates/dispositivos_list.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2365.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.importlinter`
- `AGENT_REPO_MAP.md`
- `config/settings.py`
- `config/urls.py`
- `dispositivos/apps.py`
- `dispositivos/favorite_filters.py`
- `docs/contexto/features/pr-2365-feat-dispositivos-limite-ejecutable-inicial-2309.md`
- `docs/plans/2026-08-27-issue-2309-dispositivos-relocation-design.md`
- `docs/registro/decisiones/2026-08-21-dispositivos-actor-boundary.md`
- `docs/registro/prs/PR-2365.md`
- `services/__init__.py`
- `services/dispositivos/__init__.py`
- `services/dispositivos/dispositivos/__init__.py`
- `services/dispositivos/dispositivos/adapters/__init__.py`
- `services/dispositivos/dispositivos/admin.py`
- `services/dispositivos/dispositivos/apps.py`
- `services/dispositivos/dispositivos/boundary.py`
- `services/dispositivos/dispositivos/dispositivos_filter_config.py`
- `services/dispositivos/dispositivos/favorite_filters.py`
- `services/dispositivos/dispositivos/forms.py`
- ... y 36 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2365-feat-dispositivos-limite-ejecutable-inicial-2309.md`
- `docs/plans/2026-08-27-issue-2309-dispositivos-relocation-design.md`
- `docs/registro/decisiones/2026-08-21-dispositivos-actor-boundary.md`
- `docs/registro/prs/PR-2365.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
