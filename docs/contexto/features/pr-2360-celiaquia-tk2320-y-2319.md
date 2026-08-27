# Contexto de feature PR #2360 - Celiaquia tk2320 y 2319

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2360
- Base: `development`
- Rama origen: `Celiaquia_Tk2320`
- Autor: `MariaNavarro90`

## Contexto funcional

- Celiaquía — listado de expedientes. Mejora de búsqueda y de legibilidad de estados para usuarios de Nación (coordinadores y técnicos) y de provincias.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Se modifican templates, con posible impacto visual o de composición UI.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: Mejora / evolutivo de UI. Sin cambios de modelo ni migraciones.
- Área principal declarada: celiaquia (vista y template del listado). Toca además static/custom/css/listModerno.css, compartido por listados, con una clase nueva que no altera las existentes.
- Impacto usuario declarado: Positivo — menos consultas sucesivas para encontrar un expediente y lectura más rápida del estado. Cambio de hábito a comunicar: la caja de búsqueda genérica se reemplaza por filtros por campo; quien buscaba "cualquier cosa" ahora debe elegir el campo. Los enlaces guardados con ?q= siguen funcionando.
- Riesgos / rollback: Riesgo bajo. No hay migraciones ni datos que deshacer; el rollback es revertir el commit. El riesgo principal es de adopción (desaparición del buscador de texto libre), no técnico. El filtro por técnico atraviesa una relación multivalor y el distinct() del queryset evita filas repetidas.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: celiaquia/templates/celiaquia/expediente_list.html, static/custom/css/listModerno.css

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2360.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `celiaquia/services/expediente_filter_config/__init__.py`
- `celiaquia/services/expediente_filter_config/impl.py`
- `celiaquia/templates/celiaquia/expediente_list.html`
- `celiaquia/tests/test_expediente_list_badges.py`
- `celiaquia/tests/test_expediente_list_filtros.py`
- `celiaquia/views/expediente.py`
- `docs/registro/cambios/2026-08-26-issues-2320-2319-listado-celiaquia.md`
- `static/custom/css/listModerno.css`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-08-26-issues-2320-2319-listado-celiaquia.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
