# Contexto de feature PR #2189 - [INET/VAT] Tipo de alumno VAT / Sin Plan en asistencia y exportaciones + correcciones post-#2184

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2189
- Base: `development`
- Rama origen: `TareasMati`
- Autor: `Mkdir-arg`

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
- Archivos visuales relevantes: VAT/templates/vat/oferta_institucional/asistencia_sesion.html, VAT/templates/vat/oferta_institucional/comision_detail.html, VAT/templates/vat/reportes/inscripciones_asistencia.html, centrodefamilia/templates/beneficiarios/beneficiarios_list.html, static/custom/css/cdf.css

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2189.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `VAT/forms.py`
- `VAT/services/inscripcion_service.py`
- `VAT/services/nomina_export.py`
- `VAT/services/reportes_inscripciones_asistencia.py`
- `VAT/services/tipo_alumno_service.py`
- `VAT/services/voucher_service/impl.py`
- `VAT/templates/vat/oferta_institucional/asistencia_sesion.html`
- `VAT/templates/vat/oferta_institucional/comision_detail.html`
- `VAT/templates/vat/reportes/inscripciones_asistencia.html`
- `VAT/test_comision_detail_template_compartido.py`
- `VAT/test_tipo_alumno.py`
- `VAT/tests.py`
- `VAT/views/curso.py`
- `VAT/views/oferta_institucional.py`
- `centrodefamilia/templates/beneficiarios/beneficiarios_list.html`
- `centrodefamilia/tests/test_beneficiarios_export.py`
- `docs/registro/cambios/2026-07-27-vat-comision-resultados-acta.md`
- `docs/registro/cambios/2026-07-29-cdf-beneficiarios-botones-centrados.md`
- `docs/registro/cambios/2026-07-29-vat-reintegro-voucher-rechazo.md`
- `docs/registro/cambios/2026-07-29-vat-tipo-alumno-vat-sin-plan.md`
- ... y 5 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-07-27-vat-comision-resultados-acta.md`
- `docs/registro/cambios/2026-07-29-cdf-beneficiarios-botones-centrados.md`
- `docs/registro/cambios/2026-07-29-vat-reintegro-voucher-rechazo.md`
- `docs/registro/cambios/2026-07-29-vat-tipo-alumno-vat-sin-plan.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
