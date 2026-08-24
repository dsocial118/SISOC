# Descarga de Informe Técnico para GDE

## Cambio

Se incorpora la descarga transitoria "Descargar para GDE" en el detalle de un
Informe Técnico. Toma el último archivo disponible: el DOCX editado si existe o,
en caso contrario, el borrador generado por SISOC.

Antes de responder, SISOC normaliza la geometría OOXML de cada tabla con ancho,
grilla y celdas expresados en DXA y layout fijo. No altera el contenido, los
archivos almacenados, las plantillas publicadas ni el estado del informe.

## Motivo y validación pendiente

La descarga busca evitar que las tablas se desarmen al importar el documento
como IFTEC en GDE. La compatibilidad final requiere importar casos reales de
prueba en GDE, ya que SISOC no integra ni controla ese sistema.
