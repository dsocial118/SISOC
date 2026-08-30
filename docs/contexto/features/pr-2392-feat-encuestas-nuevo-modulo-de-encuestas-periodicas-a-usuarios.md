# Contexto de feature PR #2392 - feat(encuestas): nuevo módulo de encuestas periódicas a usuarios

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2392
- Base: `development`
- Rama origen: `feature/modulo-encuestas`
- Autor: `romandolesor98`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

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
- Archivos visuales relevantes: encuestas/templates/encuestas/encuesta_form.html, encuestas/templates/encuestas/encuesta_list.html, encuestas/templates/encuestas/encuesta_resultados.html, encuestas/templates/encuestas/encuesta_segmentacion.html, encuestas/templates/encuestas/partials/campo_pregunta.html, encuestas/templates/encuestas/partials/responder_modal.html, static/custom/css/encuestaForm.css, static/custom/js/encuestaPendienteModal.js

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2392.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `AGENT_REPO_MAP.md`
- `audittrail/constants.py`
- `config/settings.py`
- `config/urls.py`
- `docker-compose.yml`
- `docker/django/entrypoint.py`
- `docs/registro/analisis/2026-08-28-modulo-encuestas.md`
- `encuestas/__init__.py`
- `encuestas/admin.py`
- `encuestas/apps.py`
- `encuestas/context_processors.py`
- `encuestas/forms.py`
- `encuestas/management/__init__.py`
- `encuestas/management/commands/__init__.py`
- `encuestas/management/commands/process_encuestas_rondas.py`
- `encuestas/middleware.py`
- `encuestas/migrations/0001_initial.py`
- `encuestas/migrations/__init__.py`
- `encuestas/models.py`
- `encuestas/services.py`
- ... y 30 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/analisis/2026-08-28-modulo-encuestas.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
