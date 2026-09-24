# Contexto de feature PR #2575 - Fixes en buscadores

## Resumen

- PR: https://github.com/secretarianaf/SISOC/pull/2575
- Base: `development`
- Rama origen: `Hogenizacion-de-buscadores`
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
- Archivos visuales relevantes: VAT/templates/vat/catalogo/modalidadcursada_list.html, VAT/templates/vat/catalogo/planversioncurricular_list.html, centrodeinfancia/templates/centrodeinfancia/centrodeinfancia_list.html, importarexpediente/templates/importarexpediente_list.html, ver_para_ser_libre/templates/ver_para_ser_libre/itinerario_list.html, ver_para_ser_libre/templates/ver_para_ser_libre/sede_list.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2575.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `VAT/catalogo_filter_config.py`
- `VAT/templates/vat/catalogo/modalidadcursada_list.html`
- `VAT/templates/vat/catalogo/planversioncurricular_list.html`
- `VAT/views/catalogo.py`
- `centrodeinfancia/filter_config.py`
- `centrodeinfancia/templates/centrodeinfancia/centrodeinfancia_list.html`
- `centrodeinfancia/views.py`
- `docs/registro/cambios/2026-09-24-buscadores-homogeneos-filtros-combinables.md`
- `importarexpediente/filter_config.py`
- `importarexpediente/templates/importarexpediente_list.html`
- `importarexpediente/views.py`
- `tests/test_buscadores_homogeneos.py`
- `ver_para_ser_libre/filter_config.py`
- `ver_para_ser_libre/templates/ver_para_ser_libre/itinerario_list.html`
- `ver_para_ser_libre/templates/ver_para_ser_libre/sede_list.html`
- `ver_para_ser_libre/views.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
