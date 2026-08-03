# Renderizado del DOCX dinámico desde una versión publicada

Fecha: 2026-07-31

## Contexto

El Informe Técnico se generaba usando paths de templates DOCX decididos por condiciones hardcodeadas. El Gestor de templates necesita que la selección dependa de una configuración publicable y que pueda evolucionar hacia un editor visual.

## Decisión

La versión publicada almacena contenido HTML y se renderiza con el contexto ya disponible para el Informe Técnico. El HTML resultante se convierte a DOCX mediante el generador existente. El motor de templates se crea sin bibliotecas ni builtins adicionales para limitar el contenido configurable a interpolación de valores del contexto.

## Consecuencias

- La generación del DOCX final no usa un fallback hardcodeado: requiere una publicación aplicable.
- La versión utilizada queda registrada junto al documento generado.
- El editor visual, catálogo guiado de variables y previsualización podrán persistir sobre este mismo contenido sin cambiar la regla de selección.
- Esta etapa no migra ni precarga los doce contenidos documentales detectados; se cargarán y publicarán desde el Gestor de templates cuando estén disponibles.
