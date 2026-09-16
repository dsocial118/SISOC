# Contexto de feature PR #2495 - Task/inet buscador ciudadano

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2495
- Base: `development`
- Rama origen: `Task/inet-buscador-ciudadano`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Se modifican templates, con posible impacto visual o de composición UI.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: VAT/templates/vat/buscador/ciudadano.html, templates/includes/sidebar/opciones.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2495.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `AGENT_REPO_MAP.md`
- `VAT/services/buscador_ciudadano_service.py`
- `VAT/services/reportes_inscripciones_asistencia.py`
- `VAT/services/vat_inscripciones_base.py`
- `VAT/templates/vat/buscador/ciudadano.html`
- `VAT/test_buscador_ciudadano.py`
- `VAT/urls.py`
- `VAT/views/buscador_ciudadano.py`
- `docs/contexto/features/pr-2495-task-inet-buscador-ciudadano.md`
- `docs/indice.md`
- `docs/plans/2026-08-13-inet-buscador-por-ciudadano-issue.md`
- `docs/plans/2026-08-13-inet-buscador-por-ciudadano-mockup.html`
- `docs/plans/inet-buscador-ciudadano/mockup-inet-buscador-por-ciudadano.pptx`
- `docs/registro/cambios/2026-08-13-inet-buscador-por-ciudadano.md`
- `docs/registro/decisiones/2026-08-13-inet-buscador-base-inscripciones-compartida.md`
- `docs/registro/prs/PR-2495.md`
- `docs/vat/manual_usuario.md`
- `templates/includes/sidebar/opciones.html`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2495-task-inet-buscador-ciudadano.md`
- `docs/plans/2026-08-13-inet-buscador-por-ciudadano-issue.md`
- `docs/plans/2026-08-13-inet-buscador-por-ciudadano-mockup.html`
- `docs/plans/inet-buscador-ciudadano/mockup-inet-buscador-por-ciudadano.pptx`
- `docs/registro/cambios/2026-08-13-inet-buscador-por-ciudadano.md`
- `docs/registro/decisiones/2026-08-13-inet-buscador-base-inscripciones-compartida.md`
- `docs/registro/prs/PR-2495.md`
- `docs/vat/manual_usuario.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
