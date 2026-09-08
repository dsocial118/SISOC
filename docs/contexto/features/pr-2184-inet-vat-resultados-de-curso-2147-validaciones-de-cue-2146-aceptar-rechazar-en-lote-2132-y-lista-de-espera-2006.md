# Contexto de feature PR #2184 - [INET/VAT] Resultados de curso (#2147), validaciones de CUE (#2146), aceptar/rechazar en lote (#2132) y lista de espera (#2006)

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2184
- Base: `development`
- Rama origen: `TareasMati`
- Autor: `Mkdir-arg`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: VAT/templates/vat/centros/centro_detail.html, VAT/templates/vat/centros/partials/centro_cursos_panel.html, VAT/templates/vat/oferta_institucional/comision_detail.html, static/custom/css/vat_design.css

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2184.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `VAT/forms.py`
- `VAT/migrations/0050_resultados_comision_curso.py`
- `VAT/models.py`
- `VAT/services/inscripcion_service.py`
- `VAT/services/resultados_comision_service.py`
- `VAT/templates/vat/centros/centro_detail.html`
- `VAT/templates/vat/centros/partials/centro_cursos_panel.html`
- `VAT/templates/vat/oferta_institucional/comision_detail.html`
- `VAT/test_comision_detail_template_compartido.py`
- `VAT/tests.py`
- `VAT/urls.py`
- `VAT/views/curso.py`
- `docs/registro/cambios/2026-07-27-vat-comision-resultados-acta.md`
- `docs/registro/cambios/2026-07-27-vat-cue-unicidad-y-prefijo-provincial.md`
- `docs/registro/cambios/2026-07-27-vat-inscriptos-aceptar-rechazar-en-lote.md`
- `docs/registro/cambios/2026-07-27-vat-lista-espera-estado-visual-checkbox.md`
- `static/custom/css/vat_design.css`
- `tests/test_vat_centro_form_state_unit.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-07-27-vat-comision-resultados-acta.md`
- `docs/registro/cambios/2026-07-27-vat-cue-unicidad-y-prefijo-provincial.md`
- `docs/registro/cambios/2026-07-27-vat-inscriptos-aceptar-rechazar-en-lote.md`
- `docs/registro/cambios/2026-07-27-vat-lista-espera-estado-visual-checkbox.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
