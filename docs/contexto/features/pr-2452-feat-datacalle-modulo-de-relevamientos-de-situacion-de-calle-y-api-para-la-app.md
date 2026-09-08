# Contexto de feature PR #2452 - feat(datacalle): módulo de relevamientos de situación de calle y API para la app

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2452
- Base: `main`
- Rama origen: `feature/datacalle-relevamientos`
- Autor: `Mkdir-arg`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Hay cambios en capa API/DRF y conviene revisar contratos de request/response.
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
- Archivos visuales relevantes: datacalle/templates/datacalle/encuesta_detail.html, datacalle/templates/datacalle/relevamiento_confirm_delete.html, datacalle/templates/datacalle/relevamiento_detail.html, datacalle/templates/datacalle/relevamiento_form.html, datacalle/templates/datacalle/relevamiento_list.html, static/custom/css/datacalle.css, templates/includes/sidebar/opciones.html, users/templates/user/user_form.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2452.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `config/settings.py`
- `config/urls.py`
- `datacalle/__init__.py`
- `datacalle/api_permissions.py`
- `datacalle/api_serializers.py`
- `datacalle/api_urls.py`
- `datacalle/api_views.py`
- `datacalle/apps.py`
- `datacalle/forms.py`
- `datacalle/instrumento/README.md`
- `datacalle/instrumento/catalogos.json`
- `datacalle/instrumento/cuestionario.json`
- `datacalle/instrumento/diccionario-respuestas.json`
- `datacalle/migrations/0001_initial.py`
- `datacalle/migrations/0002_relevamiento_localidades.py`
- `datacalle/migrations/0003_encuesta.py`
- `datacalle/migrations/__init__.py`
- `datacalle/models.py`
- `datacalle/services/__init__.py`
- `datacalle/services/encuestas.py`
- ... y 29 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/operacion/nginx/README.md`
- `docs/registro/cambios/2026-09-01-datacalle-rol-relevador-calle.md`
- `docs/registro/cambios/2026-09-03-datacalle-modulo-relevamientos.md`
- `docs/registro/cambios/2026-09-06-datacalle-casos-y-api.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
