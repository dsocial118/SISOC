# Contexto de feature PR #2568 - Task/inet mejoras septiembre 2

## Resumen

- PR: https://github.com/secretarianaf/SISOC/pull/2568
- Base: `development`
- Rama origen: `Task/inet-mejoras-septiembre-2`
- Autor: `juancruzventura-ai`

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
- Archivos visuales relevantes: VAT/templates/vat/centros/centro_detail.html, VAT/templates/vat/centros/partials/centro_cursos_panel.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2568.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `VAT/forms.py`
- `VAT/models.py`
- `VAT/templates/vat/centros/centro_detail.html`
- `VAT/templates/vat/centros/partials/centro_cursos_panel.html`
- `VAT/tests.py`
- `VAT/views/centro.py`
- `docs/registro/analisis/2026-09-23-inet-bloquear-cue-y-denominacion.md`
- `docs/registro/analisis/2026-09-23-inet-modalidad-sector-en-selector-de-plan.md`
- `docs/registro/analisis/2026-09-23-inet-quitar-usa-voucher-alta-curso.md`
- `docs/registro/analisis/2026-09-23-inet-sedes-fuera-del-departamento.md`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
