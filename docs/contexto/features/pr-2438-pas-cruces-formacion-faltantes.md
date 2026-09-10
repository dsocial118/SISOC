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
- El alcance incluye automatización o tooling de CI/CD.

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
- `.env.example`
- `.github/workflows/pr-docs.yml`
- `AGENT_REPO_MAP.md`
- `config/celery.py`
- `config/settings.py`
- `core/integrations/renaper.py`
- `core/services/renaper.py`
- `docker-compose.celery.yml`
- `docs/contexto/features/pr-2438-pas-cruces-formacion-faltantes.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/implementaciones/pas_control_mensual_celery.md`
- `docs/indice.md`
- `docs/operacion/comandos_administracion.md`
- `docs/registro/cambios/2026-09-07-pas-celery-mensual.md`
- `docs/registro/cambios/2026-09-09-pr-2438-estabilizacion-ci.md`
- `docs/registro/decisiones/2026-07-16-pas-formacion-vat.md`
- `docs/registro/decisiones/2026-07-28-pas-circuito-cruces.md`
- `docs/registro/decisiones/2026-07-29-pas-supervivencia-renaper.md`
- `docs/registro/prs/PR-2438.md`
- `pas/admin.py`
- ... y 49 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
