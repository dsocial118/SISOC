# Contexto de feature PR #2519 - fix(datacalle): revisión QA del backoffice — alcance provincial, usuarios y menú

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2519
- Base: `main`
- Rama origen: `fix/datacalle-qa-backoffice`
- Autor: `Mkdir-arg`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Hay cambios en capa API/DRF y conviene revisar contratos de request/response.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: datacalle/templates/datacalle/relevamiento_form.html, templates/includes/sidebar/opciones.html, users/templates/user/user_form.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2519.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `core/templatetags/custom_filters.py`
- `datacalle/api_views.py`
- `datacalle/apps.py`
- `datacalle/forms.py`
- `datacalle/services/__init__.py`
- `datacalle/services/encuestas.py`
- `datacalle/services/relevamientos.py`
- `datacalle/sidebar_access.py`
- `datacalle/templates/datacalle/relevamiento_form.html`
- `datacalle/urls.py`
- `datacalle/views.py`
- `docs/registro/cambios/2026-09-16-datacalle-qa-alcance-provincial.md`
- `docs/registro/cambios/2026-09-16-datacalle-qa-usuarios-y-menu.md`
- `templates/includes/sidebar/opciones.html`
- `tests/test_datacalle_api.py`
- `tests/test_datacalle_qa_usuarios.py`
- `tests/test_datacalle_relevamientos.py`
- `users/forms.py`
- `users/services.py`
- `users/services_datacalle.py`
- ... y 1 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
