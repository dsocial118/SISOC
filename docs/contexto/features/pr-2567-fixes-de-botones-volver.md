# Contexto de feature PR #2567 - Fixes de botones volver

## Resumen

- PR: https://github.com/secretarianaf/SISOC/pull/2567
- Base: `development`
- Rama origen: `Botones-Volver-#2460`
- Autor: `nehuen871`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: VAT/templates/vat/beneficiarios/beneficiarios_detail.html, VAT/templates/vat/beneficiarios/responsable_detail.html, VAT/templates/vat/catalogo/modalidadcursada_detail.html, VAT/templates/vat/catalogo/planversioncurricular_detail.html, VAT/templates/vat/catalogo/sector_detail.html, VAT/templates/vat/catalogo/subsector_detail.html, VAT/templates/vat/catalogo/titulorreferencia_detail.html, VAT/templates/vat/centros/centro_list.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2567.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `VAT/templates/vat/beneficiarios/beneficiarios_detail.html`
- `VAT/templates/vat/beneficiarios/responsable_detail.html`
- `VAT/templates/vat/catalogo/modalidadcursada_detail.html`
- `VAT/templates/vat/catalogo/planversioncurricular_detail.html`
- `VAT/templates/vat/catalogo/sector_detail.html`
- `VAT/templates/vat/catalogo/subsector_detail.html`
- `VAT/templates/vat/catalogo/titulorreferencia_detail.html`
- `VAT/templates/vat/centros/centro_list.html`
- `VAT/templates/vat/centros/usuario_generado.html`
- `VAT/templates/vat/curso/comision_curso_detail.html`
- `VAT/templates/vat/evaluacion/evaluacion_confirm_delete.html`
- `VAT/templates/vat/evaluacion/resultado_confirm_delete.html`
- `VAT/templates/vat/inscripcion_oferta/detail.html`
- `VAT/templates/vat/inscripcion_oferta/form.html`
- `VAT/templates/vat/institucion/contacto_confirm_delete.html`
- `VAT/templates/vat/institucion/identificador_confirm_delete.html`
- `VAT/templates/vat/institucion/ubicacion_confirm_delete.html`
- `VAT/templates/vat/modalidad_institucional/detail.html`
- `VAT/templates/vat/oferta_institucional/comision_confirm_delete.html`
- `VAT/templates/vat/oferta_institucional/horario_confirm_delete.html`
- ... y 114 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
