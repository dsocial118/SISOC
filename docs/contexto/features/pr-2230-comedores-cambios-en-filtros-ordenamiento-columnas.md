# Contexto de feature PR #2230 - Comedores: cambios-en-Filtros-Ordenamiento-Columnas

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2230
- Base: `development`
- Rama origen: `task/mejoras-filtros-comedores`
- Autor: `Esteban-Royo`

## Contexto funcional

- Listados y filtros de Comedores, Admisiones y Acompañamiento.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: Mejora funcional.
- Área principal declarada: Comedores.
- Impacto usuario declarado: Mejora la búsqueda, navegación y lectura de los listados.
- Riesgos / rollback: Riesgo bajo; rollback mediante reversión del código, sin cambios de base.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: acompanamientos/templates/lista_comedores.html, admisiones/templates/admisiones/admisiones_legales_list.html, admisiones/templates/admisiones/admisiones_tecnicos_list.html, templates/components/comedor_table.html, templates/components/data_table.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2230.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.importlinter`
- `AGENT_REPO_MAP.md`
- `acompanamientos/acompanamiento_service.py`
- `acompanamientos/services/__init__.py`
- `acompanamientos/services/filter_config.py`
- `acompanamientos/templates/lista_comedores.html`
- `acompanamientos/views.py`
- `acompanamientos/views_export.py`
- `admisiones/services/admisiones_service/impl.py`
- `admisiones/services/legales_service/impl.py`
- `admisiones/templates/admisiones/admisiones_legales_list.html`
- `admisiones/templates/admisiones/admisiones_tecnicos_list.html`
- `admisiones/views/web_views.py`
- `comedores/services/comedor_service/impl.py`
- `comedores/services/filter_config/impl.py`
- `core/services/favorite_filters/config.py`
- `core/services/list_ordering.py`
- `docs/registro/cambios/2026-08-03-filtros-ordenamiento-listados-comedores.md`
- `templates/components/comedor_table.html`
- `templates/components/data_table.html`
- ... y 7 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-08-03-filtros-ordenamiento-listados-comedores.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
