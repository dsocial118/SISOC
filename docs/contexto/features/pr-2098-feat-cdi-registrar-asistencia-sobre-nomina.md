# Contexto de feature PR #2098 - feat(cdi): registrar asistencia sobre nómina

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2098
- Base: `development`
- Rama origen: `codex/issue-2092-cdi-attendance-nomina`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: centrodeinfancia/templates/centrodeinfancia/centrodeinfancia_detail.html, centrodeinfancia/templates/centrodeinfancia/nomina_asistencia.html, static/custom/css/centrodeinfancia.css

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2098.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `centrodeinfancia/admin.py`
- `centrodeinfancia/migrations/0038_asistencianominacentroinfancia.py`
- `centrodeinfancia/models.py`
- `centrodeinfancia/services.py`
- `centrodeinfancia/templates/centrodeinfancia/centrodeinfancia_detail.html`
- `centrodeinfancia/templates/centrodeinfancia/nomina_asistencia.html`
- `centrodeinfancia/tests/test_asistencia_nomina.py`
- `centrodeinfancia/tests/test_asistencia_trabajador.py`
- `centrodeinfancia/urls.py`
- `centrodeinfancia/views.py`
- `docs/plans/2026-07-17-issue-2092-cdi-asistencia-nomina-design.md`
- `docs/registro/cambios/2026-07-17-cdi-asistencia-nomina.md`
- `static/custom/css/centrodeinfancia.css`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/plans/2026-07-17-issue-2092-cdi-asistencia-nomina-design.md`
- `docs/registro/cambios/2026-07-17-cdi-asistencia-nomina.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
