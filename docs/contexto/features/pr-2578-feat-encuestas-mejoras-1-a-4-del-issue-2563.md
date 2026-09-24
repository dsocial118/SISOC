# Contexto de feature PR #2578 - feat(encuestas): mejoras 1 a 4 del issue #2563

## Resumen

- PR: https://github.com/secretarianaf/SISOC/pull/2578
- Base: `development`
- Rama origen: `Fixex-24-09`
- Autor: `PabloCao1`

## Contexto funcional

- mejoras 1 a 4 del issue #2563; el punto 5 de aprobación de publicación sigue en análisis.

## Arquitectura tocada

- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: feature y mejoras de usabilidad.
- Área principal declarada: encuestas.
- Impacto usuario declarado: menos carga manual entre ambientes, posibilidad de descartar una ronda opcional y formularios más claros.
- Riesgos / rollback: aplicar la migración antes de servir el código actualizado y reiniciar web/worker; el JSON con segmentación contiene documentos personales; revertir la migración elimina modalidad opcional y descartes.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: encuestas/templates/encuestas/encuesta_form.html, encuestas/templates/encuestas/encuesta_list.html, encuestas/templates/encuestas/encuesta_segmentacion.html, encuestas/templates/encuestas/partials/responder_modal.html, static/custom/css/encuestaForm.css, static/custom/css/encuestaResponder.css, templates/components/search_bar.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2578.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `AGENT_REPO_MAP.md`
- `docs/implementaciones/encuestas.md`
- `docs/registro/cambios/2026-09-24-encuestas-mejoras-2563.md`
- `docs/tmp/encuesta-prueba-con-segmentacion.json`
- `docs/tmp/encuesta-prueba-error.json`
- `docs/tmp/encuesta-prueba.json`
- `encuestas/forms.py`
- `encuestas/migrations/0003_encuesta_opcional.py`
- `encuestas/models.py`
- `encuestas/services.py`
- `encuestas/templates/encuestas/encuesta_form.html`
- `encuestas/templates/encuestas/encuesta_list.html`
- `encuestas/templates/encuestas/encuesta_segmentacion.html`
- `encuestas/templates/encuestas/partials/responder_modal.html`
- `encuestas/tests/test_encuestas_opcionales.py`
- `encuestas/tests/test_encuestas_portabilidad.py`
- `encuestas/urls.py`
- `encuestas/views.py`
- `static/custom/css/encuestaForm.css`
- `static/custom/css/encuestaResponder.css`
- ... y 1 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
