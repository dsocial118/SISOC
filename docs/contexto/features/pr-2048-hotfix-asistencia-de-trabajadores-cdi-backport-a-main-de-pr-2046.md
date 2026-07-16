# Contexto de feature PR #2048 - hotfix: asistencia de trabajadores CDI (backport a main de PR #2046)

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2048
- Base: `main`
- Rama origen: `versionNuevaCDF-main`
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
- Archivos visuales relevantes: centrodeinfancia/templates/centrodeinfancia/centrodeinfancia_detail.html, centrodeinfancia/templates/centrodeinfancia/destinatario_form.html, centrodeinfancia/templates/centrodeinfancia/nomina_detail.html, centrodeinfancia/templates/centrodeinfancia/trabajador_asistencia.html, centrodeinfancia/templates/centrodeinfancia/trabajador_form.html, static/custom/css/cdf.css, static/custom/css/centrodeinfancia.css

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2048.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `CHANGELOG.md`
- `centrodeinfancia/migrations/0036_asistenciatrabajador.py`
- `centrodeinfancia/models.py`
- `centrodeinfancia/templates/centrodeinfancia/centrodeinfancia_detail.html`
- `centrodeinfancia/templates/centrodeinfancia/destinatario_form.html`
- `centrodeinfancia/templates/centrodeinfancia/nomina_detail.html`
- `centrodeinfancia/templates/centrodeinfancia/trabajador_asistencia.html`
- `centrodeinfancia/templates/centrodeinfancia/trabajador_form.html`
- `centrodeinfancia/tests/test_asistencia_trabajador.py`
- `centrodeinfancia/tests/test_formulario_cdi_views.py`
- `centrodeinfancia/urls.py`
- `centrodeinfancia/views.py`
- `docs/contexto/features/pr-2046-hotfix.md`
- `docs/registro/cambios/2026-07-13-cdi-asistencia-trabajadores.md`
- `docs/registro/cambios/2026-07-13-cdi-rediseno-detalle-nomina.md`
- `docs/registro/prs/PR-2046.md`
- `docs/registro/releases/pending/2026-07-15-pr-2046.md`
- `static/custom/css/cdf.css`
- `static/custom/css/centrodeinfancia.css`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2046-hotfix.md`
- `docs/registro/cambios/2026-07-13-cdi-asistencia-trabajadores.md`
- `docs/registro/cambios/2026-07-13-cdi-rediseno-detalle-nomina.md`
- `docs/registro/prs/PR-2046.md`
- `docs/registro/releases/pending/2026-07-15-pr-2046.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
