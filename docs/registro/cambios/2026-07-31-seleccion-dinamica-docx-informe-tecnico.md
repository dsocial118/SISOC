# Selección dinámica del DOCX de Informe Técnico

Fecha: 2026-07-31

## Cambio

Al finalizar un Informe Técnico de Comedores, SISOC resuelve la única versión de template publicada que coincide con las validaciones de su admisión y genera el DOCX desde ese contenido.

Las validaciones consideradas son el tipo de admisión y de convenio, más Ex PNUD y estado PNUD para incorporaciones, o tipo de renovación y estado de financiamiento para renovaciones.

## Comportamiento ante ausencia de configuración

Si faltan validaciones, no se genera el DOCX ni se finaliza la admisión. El
Informe Técnico queda guardado como borrador y editable para corregirlas.

Si las validaciones están completas pero no existe una versión publicada
coincidente, tampoco se genera el DOCX ni se finaliza la admisión. El Informe
Técnico queda como borrador hasta que los referentes publiquen una versión
aplicable.

## Trazabilidad

El documento generado conserva la referencia a la plantilla lógica y a la versión publicada con la que fue producido.

## Alcance preservado

No se modifican las reglas existentes de documentación obligatoria ni la determinación de `tipo_convenio` que proviene del Legajo Organización.
