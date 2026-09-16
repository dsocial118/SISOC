# Contexto de feature PR #2509 - feat(core): mapa de arquitectura regenerado en cada arranque

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2509
- Base: `development`
- Rama origen: `juanikitro/docs-sisoc-module-map`
- Autor: `juanikitro`

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
- Archivos visuales relevantes: core/templates/core/mapa_arquitectura.html, static/arquitectura/mapa.css, static/arquitectura/mapa.js, templates/changelog.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2509.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.gitignore`
- `core/management/commands/generar_mapa_arquitectura.py`
- `core/templates/core/mapa_arquitectura.html`
- `core/urls.py`
- `core/views.py`
- `docker/django/entrypoint.py`
- `docs/arquitectura/grafo_sisoc.json`
- `docs/arquitectura/mapa_sisoc.html`
- `docs/registro/cambios/2026-09-15-mapa-arquitectura.md`
- `scripts/arquitectura/generar_mapa.py`
- `static/arquitectura/mapa.css`
- `static/arquitectura/mapa.js`
- `templates/changelog.html`
- `tests/test_docker_entrypoint_unit.py`
- `tests/test_mapa_arquitectura_generador.py`
- `tests/test_mapa_arquitectura_smoke.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
