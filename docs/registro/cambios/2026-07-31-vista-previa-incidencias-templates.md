# Vista previa e incidencias de templates de Informe Técnico

Fecha: 2026-07-31

## Vista previa temporal

El técnico puede descargar una vista previa del DOCX mientras su Informe Técnico siga en borrador y exista una versión publicada aplicable. El archivo usa los datos reales del informe, incorpora la marca de agua `VISTA PREVIA — DOCUMENTO NO VÁLIDO` y no se persiste en la admisión ni altera estados.

El Gestor de templates también puede probar una versión en borrador o publicada indicando el ID de un Informe Técnico existente. Esto permite revisar el resultado antes de publicar.

## Reporte de configuración faltante

Cuando las validaciones de la admisión están completas pero no existe una versión publicada para su combinación, el técnico recibe un detalle copiable y puede reportar el faltante.

El sistema agrupa los reportes mientras la incidencia permanezca pendiente o en análisis. Cada caso conserva los IDs de admisión e informe, datos de comedor, organización y programa, respuestas evaluadas, usuario, fecha y estado de admisión. Si una incidencia se resuelve o descarta y la combinación vuelve a reportarse, se abre una nueva incidencia enlazada con la anterior.

## Gestión

El rol `Gestor de templates` dispone del listado `Incidencias de templates` para filtrar, consultar los casos agrupados, cambiar estado, registrar observaciones y vincular una plantilla. No se agregan notificaciones ni un canal de conversación.
