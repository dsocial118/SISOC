# Contexto de feature PR #2543 - chore(sync): integrar main en development

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2543
- Base: `development`
- Rama origen: `automation/sync-main-to-development`
- Autor: `sisoc-release-automation[bot]`

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
- Archivos visuales relevantes: datacalle/templates/datacalle/encuesta_detail.html, datacalle/templates/datacalle/relevamiento_detail.html, datacalle/templates/datacalle/relevamiento_form.html, datacalle/templates/datacalle/relevamiento_list.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2543.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `CHANGELOG.md`
- `audittrail/constants.py`
- `datacalle/api_permissions.py`
- `datacalle/api_serializers.py`
- `datacalle/api_views.py`
- `datacalle/instrumento/catalogos.json`
- `datacalle/instrumento/cuestionario.json`
- `datacalle/instrumento/diccionario-respuestas.json`
- `datacalle/models.py`
- `datacalle/services/__init__.py`
- `datacalle/services/encuestas.py`
- `datacalle/services/relevamientos.py`
- `datacalle/templates/datacalle/encuesta_detail.html`
- `datacalle/templates/datacalle/relevamiento_detail.html`
- `datacalle/templates/datacalle/relevamiento_form.html`
- `datacalle/templates/datacalle/relevamiento_list.html`
- `datacalle/urls.py`
- `datacalle/views.py`
- `docs/contexto/features/pr-2542-fix-datacalle-revision-qa-del-backoffice-tres-roles-con-provincia-unica.md`
- `docs/registro/cambios/2026-09-17-datacalle-qa-segundo-bloque.md`
- ... y 17 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
