# Contexto de feature PR #2365 - feat(dispositivos): límite ejecutable inicial (#2309)

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2365
- Base: `development`
- Rama origen: `codex/issue-2309-executable-boundary`
- Autor: `juanikitro`

## Contexto funcional

- desacoplar actor, permisos y territorio sin alterar el CRUD ni extraer todavía el runtime.

## Arquitectura tocada

- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: boundary ejecutable, primer corte.
- Área principal declarada: Dispositivos.
- Impacto usuario declarado: se preservan rutas, permisos y alcance territorial.
- Riesgos / rollback: una adaptación incorrecta podría cambiar permisos o alcance territorial; revertir el commit conserva rutas, tablas, FKs y escritor del monolito.

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2365.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.importlinter`
- `AGENT_REPO_MAP.md`
- `dispositivos/adapters/__init__.py`
- `dispositivos/adapters/monolith_filters.py`
- `dispositivos/adapters/monolith_permissions.py`
- `dispositivos/adapters/monolith_session.py`
- `dispositivos/adapters/monolith_territorial.py`
- `dispositivos/boundary.py`
- `dispositivos/favorite_filters.py`
- `dispositivos/forms.py`
- `dispositivos/migrations/0006_versionproyeccionterritorial_and_more.py`
- `dispositivos/models.py`
- `dispositivos/ports.py`
- `dispositivos/services.py`
- `dispositivos/territorial_projection.py`
- `dispositivos/tests/test_dispositivos_services.py`
- `dispositivos/tests/test_territorial_projection.py`
- `dispositivos/urls.py`
- `dispositivos/views.py`
- `docs/contexto/features/pr-2365-feat-dispositivos-limite-ejecutable-inicial-2309.md`
- ... y 2 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2365-feat-dispositivos-limite-ejecutable-inicial-2309.md`
- `docs/registro/decisiones/2026-08-21-dispositivos-actor-boundary.md`
- `docs/registro/prs/PR-2365.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
