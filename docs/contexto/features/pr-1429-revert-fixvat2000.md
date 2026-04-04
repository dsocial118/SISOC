# Contexto de feature PR #1429 - Revert "FIXVAT2000"

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/1429
- Base: `main`
- Rama origen: `revert-1428-development`
- Autor: `dsocial118`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Hay cambios en capa API/DRF y conviene revisar contratos de request/response.
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
- Archivos visuales relevantes: VAT/templates/vat/catalogo/planversioncurricular_detail.html, VAT/templates/vat/catalogo/planversioncurricular_form.html, VAT/templates/vat/centros/centro_detail.html, VAT/templates/vat/curso/comision_curso_detail.html, VAT/templates/vat/curso/curso_form.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-1429.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `VAT/api_views.py`
- `VAT/forms.py`
- `VAT/migrations/0031_remove_curso_programa.py`
- `VAT/migrations/0032_move_curso_ubicacion_to_comisioncurso.py`
- `VAT/models.py`
- `VAT/serializers.py`
- `VAT/templates/vat/catalogo/planversioncurricular_detail.html`
- `VAT/templates/vat/catalogo/planversioncurricular_form.html`
- `VAT/templates/vat/centros/centro_detail.html`
- `VAT/templates/vat/curso/comision_curso_detail.html`
- `VAT/templates/vat/curso/curso_form.html`
- `VAT/tests.py`
- `VAT/views/centro.py`
- `VAT/views/curso.py`
- `docs/registro/cambios/2026-04-03-vat-centro-edicion-sin-provincia.md`
- `docs/registro/cambios/2026-04-04-vat-comision-curso-codigo-nombre-automaticos.md`
- `docs/registro/cambios/2026-04-04-vat-comision-curso-ubicacion.md`
- `docs/registro/cambios/2026-04-04-vat-curso-programa-derivado.md`
- `docs/registro/cambios/2026-04-04-vat-planes-curriculares-nombre.md`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-04-03-vat-centro-edicion-sin-provincia.md`
- `docs/registro/cambios/2026-04-04-vat-comision-curso-codigo-nombre-automaticos.md`
- `docs/registro/cambios/2026-04-04-vat-comision-curso-ubicacion.md`
- `docs/registro/cambios/2026-04-04-vat-curso-programa-derivado.md`
- `docs/registro/cambios/2026-04-04-vat-planes-curriculares-nombre.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
