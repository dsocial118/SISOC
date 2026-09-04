# Contexto de feature PR #2438 - PAS: Cruces-formacion-Faltantes

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2438
- Base: `development`
- Rama origen: `task/PAS-Cruces-Renaper-Formacion-dev`
- Autor: `Esteban-Royo`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: pas/templates/pas/area.html, pas/templates/pas/cruces.html, pas/templates/pas/includes/formacion_personas.html, pas/templates/pas/includes/workflow_nav.html, pas/templates/pas/persona_confirm_delete.html, pas/templates/pas/persona_detail.html, pas/templates/pas/persona_form.html, pas/templates/pas/persona_list.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2438.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `AGENT_REPO_MAP.md`
- `docs/indice.md`
- `docs/operacion/comandos_administracion.md`
- `docs/registro/decisiones/2026-07-16-pas-formacion-vat.md`
- `docs/registro/decisiones/2026-07-28-pas-circuito-cruces.md`
- `docs/registro/decisiones/2026-07-29-pas-supervivencia-renaper.md`
- `pas/admin.py`
- `pas/apps.py`
- `pas/favorite_filters.py`
- `pas/forms.py`
- `pas/management/__init__.py`
- `pas/management/commands/__init__.py`
- `pas/management/commands/sincronizar_supervivencia_pas.py`
- `pas/migrations/0004_pascircuitomensual.py`
- `pas/migrations/0005_pascontrolrenaper_pasincompatibilidad.py`
- `pas/models.py`
- `pas/services/cruces_service.py`
- `pas/services/filter_config.py`
- `pas/services/formacion_service.py`
- `pas/services/persona_service.py`
- ... y 25 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/operacion/comandos_administracion.md`
- `docs/registro/decisiones/2026-07-16-pas-formacion-vat.md`
- `docs/registro/decisiones/2026-07-28-pas-circuito-cruces.md`
- `docs/registro/decisiones/2026-07-29-pas-supervivencia-renaper.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
