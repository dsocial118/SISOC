# Contexto de feature PR #2222 - feat(comedores): agregar etiqueta CARITAS

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2222
- Base: `development`
- Rama origen: `codex/issue-2216-caritas`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Hay cambios en capa API/DRF y conviene revisar contratos de request/response.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: comedores/templates/comedor/comedor_detail.html, comedores/templates/comedor/comedor_form.html, organizaciones/templates/organizacion_detail.html, static/custom/css/comedor_detail.css

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2222.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `comedores/api_serializers.py`
- `comedores/forms/comedor_form.py`
- `comedores/migrations/0053_issue_2216_es_caritas.py`
- `comedores/models.py`
- `comedores/templates/comedor/comedor_detail.html`
- `comedores/templates/comedor/comedor_form.html`
- `docs/registro/cambios/2026-08-04-etiqueta-caritas-comedores.md`
- `organizaciones/templates/organizacion_detail.html`
- `requirements/lint.txt`
- `static/custom/css/comedor_detail.css`
- `tests/test_comedor_form_unit.py`
- `tests/test_issue_2163_categoria_espacio.py`
- `tests/test_pwa_comedores_api.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-08-04-etiqueta-caritas-comedores.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
