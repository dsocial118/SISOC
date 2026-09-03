# Contexto de feature PR #2429 - Celiaquia tk2318

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2429
- Base: `development`
- Rama origen: `celiaquia_Tk2318`
- Autor: `MariaNavarro90`

## Contexto funcional

- Celiaquía — revisión técnica de legajos. El técnico registra observaciones estructuradas y esas mismas observaciones son las que se le comunican a la Provincia al subsanar o rechazar, sin volver a redactarlas.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: Evolutivo funcional (incluye dos correcciones detectadas durante la implementación).
- Área principal declarada: celiaquia — detalle de expediente, revisión de legajos.
- Impacto usuario declarado: Técnico y Coordinador dejan de reescribir motivos y cargan observaciones de un catálogo cerrado. La Provincia recibe un texto uniforme y trazable. El comentario de texto libre y el adjunto se retiran del formulario (el requerimiento enumera cuatro campos y ninguno es texto suelto); el endpoint los sigue aceptando, así que nada externo se rompe.
- Riesgos / rollback: Riesgo bajo. La migración es aditiva, con todos los campos nulos y sin RunPython: no modifica ni una fila existente y revierte sin pérdida de datos. Se conservan los campos legacy, así que reportes y flujos existentes siguen leyendo lo mismo. Los legajos que ya están en SUBSANAR con motivo libre quedan como están, cubiertos por el fallback. El rollback es revertir los commits y aplicar migrate celiaquia 0006.

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
- `docs/contexto/features/pr-2429-celiaquia-tk2318.md`
- `docs/registro/cambios/2026-09-03-celiaquia-comentarios-tecnicos-subsanacion.md`
- `docs/registro/prs/PR-2429.md`
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
- `docs/contexto/features/pr-2429-celiaquia-tk2318.md`
- `docs/registro/cambios/2026-09-03-celiaquia-comentarios-tecnicos-subsanacion.md`
- `docs/registro/prs/PR-2429.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
