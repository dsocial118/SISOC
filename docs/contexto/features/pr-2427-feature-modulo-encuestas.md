# Contexto de feature PR #2427 - Feature/modulo encuestas

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2427
- Base: `development`
- Rama origen: `feature/modulo-encuestas`
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
- Archivos visuales relevantes: encuestas/templates/encuestas/encuesta_form.html, encuestas/templates/encuestas/encuesta_resultados.html, static/custom/css/encuestaForm.css, static/custom/css/encuestaResultados.css, static/custom/js/encuestaPreguntasBuilder.js

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2427.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `docs/contexto/features/pr-2427-feature-modulo-encuestas.md`
- `docs/registro/analisis/2026-08-28-modulo-encuestas.md`
- `docs/registro/prs/PR-2427.md`
- `encuestas/migrations/0002_opcionpregunta_puntaje_pregunta_pondera_and_more.py`
- `encuestas/models.py`
- `encuestas/services.py`
- `encuestas/services_resultados.py`
- `encuestas/templates/encuestas/encuesta_form.html`
- `encuestas/templates/encuestas/encuesta_resultados.html`
- `encuestas/tests/test_encuestas_puntaje.py`
- `encuestas/tests/test_encuestas_responder.py`
- `encuestas/tests/test_encuestas_services.py`
- `encuestas/validators.py`
- `encuestas/views.py`
- `static/custom/css/encuestaForm.css`
- `static/custom/css/encuestaResultados.css`
- `static/custom/js/encuestaPreguntasBuilder.js`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2427-feature-modulo-encuestas.md`
- `docs/registro/analisis/2026-08-28-modulo-encuestas.md`
- `docs/registro/prs/PR-2427.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
