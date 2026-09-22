# Contexto de feature PR #2550 - Celiaquia tk 2152

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2550
- Base: `development`
- Rama origen: `CeliaquiaTk_2152`
- Autor: `MariaNavarro90`

## Contexto funcional

- Celiaquía — validación RENAPER de un legajo. Cuando el domicilio de RENAPER no coincide con el presentado por el beneficiario, el técnico necesita saber a qué versión del DNI corresponde el dato del servicio para decidir cuál es el vigente.

## Arquitectura tocada

- Se modifican templates, con posible impacto visual o de composición UI.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: feature
- Área principal declarada: celiaquia — validación RENAPER (vista, template y JS; sin modelos ni migraciones)
- Impacto usuario declarado: Sólo lectura y sólo para técnicos y coordinadores que usan la validación RENAPER. No cambia datos, estados ni flujos: agrega información al modal existente. Por la medición de producción, la franja va a verse en prácticamente todas las validaciones.
- Riesgos / rollback: Bajo. Sin migraciones ni cambios de modelo, el rollback es revertir el commit. No se tocó el mapeo compartido de core, así que otras apps no se ven afectadas. El campo se lee de forma defensiva: si el servicio dejara de mandarlo o cambiara el formato, la UI oculta el bloque o muestra el valor crudo, sin romper la validación.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: celiaquia/templates/celiaquia/expediente_detail.html, static/custom/js/expediente_detail.js

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2550.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `celiaquia/templates/celiaquia/expediente_detail.html`
- `celiaquia/tests/test_validacion_renaper_ejemplar.py`
- `celiaquia/views/validacion_renaper.py`
- `docs/contexto/features/pr-2550-celiaquia-tk-2152.md`
- `docs/registro/cambios/2026-09-21-2152-fecha-emision-dni-renaper.md`
- `docs/registro/prs/PR-2550.md`
- `static/custom/js/expediente_detail.js`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
