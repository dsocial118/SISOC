# Catálogo inicial de variables para templates de Informe Técnico

## Cambio visible

El Gestor de templates incorpora el catálogo **Variables documentales** y el
editor de una versión en borrador muestra sus variables disponibles por
categoría. La persona gestora puede buscar una variable, insertarla con clic o
arrastrarla al cursor del contenido, y activar o inactivar variables desde el
listado.

La migración `0073_variabletemplateinformetecnico` precarga las 106
expresiones usadas por los cuatro modelos DOCX de Informe Técnico existentes:
incorporación base/jurídico y renovación base/jurídico.

La migración `0074_variables_compatibilidad_templates_informe_tecnico` agrega
además las 21 variables planas que el contexto del generador ya exponía en la
primera versión del Gestor. Así, contenidos creados con expresiones como
`{{ nombre_espacio }}` siguen siendo publicables.

## Regla de publicación

Un borrador se puede guardar aunque todavía contenga una variable pendiente de
definir. Al publicarlo, SISOC verifica que todas las expresiones `{{ ... }}`
usadas estén activas en el catálogo. Esto evita que un template operativo use
un dato inexistente o deshabilitado.

## Alcance

El catálogo sólo expone datos ya presentes en el contexto real que genera el
DOCX. No agrega campos al Informe Técnico ni modifica los requisitos
documentales de la admisión.
