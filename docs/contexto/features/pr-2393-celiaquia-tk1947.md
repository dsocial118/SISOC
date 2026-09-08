# Contexto de feature PR #2393 - Celiaquia tk1947

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2393
- Base: `development`
- Rama origen: `Celiaquia_Tk1947`
- Autor: `MariaNavarro90`

## Contexto funcional

- Celiaquía — detalle del expediente. Mejora de legibilidad para las tareas de control y validación de completitud de un expediente.

## Arquitectura tocada

- Se modifican templates, con posible impacto visual o de composición UI.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: Mejora de UI. Sin cambios de modelo ni migraciones.
- Área principal declarada: celiaquia (vista y template del detalle de expediente).
- Impacto usuario declarado: Positivo y sin contrapartidas. Permite conocer de inmediato cuántas personas contiene un expediente, sin contar filas a mano. No modifica ningún flujo existente.
- Riesgos / rollback: Riesgo mínimo: es un dato de solo lectura derivado de un aggregate que la vista ya ejecutaba, por lo que tampoco agrega carga. Rollback: revertir el commit; no hay migraciones ni datos que deshacer.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: celiaquia/templates/celiaquia/expediente_detail.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2393.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `celiaquia/templates/celiaquia/expediente_detail.html`
- `celiaquia/tests/test_expediente_detail_total_legajos.py`
- `celiaquia/views/expediente.py`
- `docs/registro/cambios/2026-08-28-issue-1947-total-legajos-expediente.md`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-08-28-issue-1947-total-legajos-expediente.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
