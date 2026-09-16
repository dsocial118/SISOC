# Contexto de feature PR #2517 - CDI reportes: ajustes de pantalla y permiso propio de acceso (#2508)

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2517
- Base: `development`
- Rama origen: `juanikitro/cdi-reportes-ajustes-2508`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: centrodeinfancia/templates/centrodeinfancia/reportes.html, templates/includes/sidebar/opciones.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2517.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `centrodeinfancia/services_reportes.py`
- `centrodeinfancia/templates/centrodeinfancia/reportes.html`
- `centrodeinfancia/tests/test_reportes.py`
- `centrodeinfancia/urls.py`
- `centrodeinfancia/views_reportes.py`
- `docs/implementaciones/centrodeinfancia_reportes.md`
- `docs/registro/cambios/2026-09-15-issue-2508-cdi-reportes-fase-2.md`
- `templates/includes/sidebar/opciones.html`
- `users/bootstrap/groups_seed.py`
- `users/migrations/0052_bootstrap_reportes_cdi_permission.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
