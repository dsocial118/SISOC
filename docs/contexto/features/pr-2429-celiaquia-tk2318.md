# Contexto de feature PR #2429 - Celiaquia tk2318

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2429
- Base: `development`
- Rama origen: `celiaquia_Tk2318`
- Autor: `MariaNavarro90`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: celiaquia/templates/celiaquia/expediente_detail.html, static/custom/css/listModerno.css, static/custom/js/expediente_detail.js, static/custom/js/expediente_detail_config.js, static/custom/js/legajo_comentarios.js

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2429.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `celiaquia/comentarios_tecnicos.py`
- `celiaquia/migrations/0007_comentarios_tecnicos.py`
- `celiaquia/models.py`
- `celiaquia/services/comentarios_tecnicos_service/__init__.py`
- `celiaquia/services/comentarios_tecnicos_service/impl.py`
- `celiaquia/templates/celiaquia/expediente_detail.html`
- `celiaquia/tests/test_comentarios_tecnicos_flujo.py`
- `celiaquia/tests/test_comentarios_tecnicos_service.py`
- `celiaquia/urls.py`
- `celiaquia/views/comentarios.py`
- `celiaquia/views/expediente.py`
- `docs/registro/cambios/2026-09-03-celiaquia-comentarios-tecnicos-subsanacion.md`
- `static/custom/css/listModerno.css`
- `static/custom/js/expediente_detail.js`
- `static/custom/js/expediente_detail_config.js`
- `static/custom/js/legajo_comentarios.js`
- `tests/test_celiaquia_expediente_view_helpers_unit.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-09-03-celiaquia-comentarios-tecnicos-subsanacion.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
