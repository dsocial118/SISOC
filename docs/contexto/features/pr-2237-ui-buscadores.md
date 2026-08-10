# Contexto de feature PR #2237 - UI buscadores

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2237
- Base: `development`
- Rama origen: `UI_buscadores`
- Autor: `MariaNavarro90`

## Contexto funcional

- Buscadores y filtros de listados en toda la aplicación.

## Arquitectura tocada

- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: Feature + refactor de UI. Incluye corrección de bugs encontrados en el camino.
- Área principal declarada: Componente compartido search_bar / listados transversales.
- Impacto usuario declarado: Alto y visible. Cambia el aspecto y la interacción de todos los listados. Se pierden la búsqueda por campo vacío, por rango y por exclusión, la combinación con OR, y los filtros favoritos dejan de estar accesibles desde la UI.
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: VAT/templates/vat/centros/centro_list.html, celiaquia/templates/celiaquia/expediente_list.html, ciudadanos/templates/ciudadanos/ciudadano_list.html, comedores/templates/comedor/actividades_pnud_list.html, insumos/templates/insumos/insumos_list.html, static/custom/css/comedoresSearchBar.css, static/custom/css/hitos.css, static/custom/css/listModerno.css

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2237.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `VAT/templates/vat/centros/centro_list.html`
- `celiaquia/templates/celiaquia/expediente_list.html`
- `celiaquia/views/expediente.py`
- `centrodefamilia/tests/test_beneficiarios_export.py`
- `ciudadanos/ciudadanos_filter_config.py`
- `ciudadanos/templates/ciudadanos/ciudadano_list.html`
- `ciudadanos/views.py`
- `comedores/templates/comedor/actividades_pnud_list.html`
- `comunicados/views.py`
- `docs/registro/cambios/2026-07-31-buscador-transversal-lupa-y-cta.md`
- `insumos/templates/insumos/insumos_list.html`
- `insumos/views.py`
- `static/custom/css/comedoresSearchBar.css`
- `static/custom/css/hitos.css`
- `static/custom/css/listModerno.css`
- `static/custom/css/poncho.css`
- `static/custom/css/poncho_listados.css`
- `static/custom/css/ver_para_ser_libre.css`
- `static/custom/js/advanced_filters.js`
- `static/custom/js/favorite_filters.js`
- ... y 6 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-07-31-buscador-transversal-lupa-y-cta.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
