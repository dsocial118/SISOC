# Contexto de feature PR #2468 - fix(admisiones): reubicar descarga GDE validada

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2468
- Base: `development`
- Rama origen: `codex/issue-2443-gde`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: admisiones/templates/admisiones/includes/boton_tecnicos.html, admisiones/templates/admisiones/informe_tecnico_detalle.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2468.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `admisiones/services/admisiones_service/impl.py`
- `admisiones/services/informes_service/impl.py`
- `admisiones/templates/admisiones/includes/boton_tecnicos.html`
- `admisiones/templates/admisiones/informe_tecnico_detalle.html`
- `admisiones/templatetags/admisiones_tags.py`
- `admisiones/views/web_views.py`
- `docs/plans/2026-09-08-issue-2443-gde-design.md`
- `docs/registro/cambios/2026-09-08-informe-tecnico-gde.md`
- `tests/test_admisiones_service_botones_characterization_db.py`
- `tests/test_admisiones_web_views_unit.py`
- `tests/test_informes_service_unit.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/plans/2026-09-08-issue-2443-gde-design.md`
- `docs/registro/cambios/2026-09-08-informe-tecnico-gde.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
