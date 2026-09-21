# Contexto de feature PR #2546 - Celiaquia tk 2362

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2546
- Base: `development`
- Rama origen: `CeliaquiaTk_2362`
- Autor: `MariaNavarro90`

## Contexto funcional

- Celiaquía — reporte de provincias (/reporter-provincias/). Producto necesita saber cuántas personas únicas y cuántas duplas hijo–responsable hay alcanzadas entre los legajos aprobados, dato que hoy exige cruzar a mano el grupo familiar de cada caso.

## Arquitectura tocada

- Se modifican templates, con posible impacto visual o de composición UI.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: feature
- Área principal declarada: celiaquia — reporte de provincias (vista, template y estilos; sin modelos ni migraciones)
- Impacto usuario declarado: Sólo lectura y sólo para quienes acceden al reporte de provincias. No cambia datos, estados ni flujos: agrega información al panel de aprobados y una columna al listado. Los totales generales de legajos se mantienen igual.
- Riesgos / rollback: Bajo. No hay migraciones ni cambios de modelo, así que el rollback es revertir el commit. El riesgo acotado es de interpretación, no técnico: si producto define la dupla distinto (contar por par en vez de por hijo, o no exigir que el responsable esté aprobado), cambia el número — ambos criterios están aislados en _build_clasificacion_aprobados y son de una línea. En performance no hay impacto sobre el panel (reusa la consulta existente); el detalle suma dos consultas acotadas a los 12 registros de la página.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: celiaquia/templates/celiaquia/reporter_provincias.html, static/custom/css/reporter_provincias.css

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2546.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `celiaquia/templates/celiaquia/reporter_provincias.html`
- `celiaquia/tests/test_reporter_provincias.py`
- `celiaquia/views/reporter_provincias.py`
- `docs/contexto/features/pr-2546-celiaquia-tk-2362.md`
- `docs/registro/cambios/2026-09-21-2362-duplas-hijo-responsable-reporter.md`
- `docs/registro/prs/PR-2546.md`
- `static/custom/css/reporter_provincias.css`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
