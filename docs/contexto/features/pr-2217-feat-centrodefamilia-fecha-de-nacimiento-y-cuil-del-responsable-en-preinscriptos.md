# Contexto de feature PR #2217 - feat(centrodefamilia): fecha de nacimiento y CUIL del responsable en preinscriptos

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2217
- Base: `development`
- Rama origen: `cdf-beneficiarios-fecha-nacimiento-cuil-responsable`
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
- Archivos visuales relevantes: centrodefamilia/templates/beneficiarios/beneficiarios_list.html, static/custom/js/listSort.js, tests/js/test_list_sort_dates.js

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2217.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `centrodefamilia/services/beneficiarios_service/impl.py`
- `centrodefamilia/templates/beneficiarios/beneficiarios_list.html`
- `centrodefamilia/tests/test_beneficiarios_export.py`
- `centrodefamilia/views/beneficiarios.py`
- `centrodefamilia/views/beneficiarios_export.py`
- `docs/registro/cambios/2026-07-27-cdf-exportacion-beneficiarios.md`
- `docs/registro/cambios/2026-07-31-cdf-beneficiarios-columnas-y-export-sse.md`
- `static/custom/js/listSort.js`
- `tests/js/test_list_sort_dates.js`
- `tests/test_beneficiarios_service_unit.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-07-27-cdf-exportacion-beneficiarios.md`
- `docs/registro/cambios/2026-07-31-cdf-beneficiarios-columnas-y-export-sse.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
