# Issue 2305: evolutivos de rendiciones mensuales

## Alcance

Se coordinó el flujo web y PWA de rendiciones: catálogos cerrados de convenio y
número, período mensual progresivo, categorías múltiples, separación de
comprobantes, confirmación de envío, solicitudes de documentos faltantes,
subsanación ampliada y edición protegida de datos generales.

El listado global incorpora exportación CSV sobre el resultado filtrado,
configuración de columnas, filtro y pill de etapa. La descarga PDF usa un nombre
descriptivo con proyecto, convenio, número y período.

## Datos y compatibilidad

La migración `0017` agrega el nombre de rendición, el permiso
`edit_rendicion_data` y `SolicitudDocumentoFaltante`. Los documentos históricos
de categoría `comprobantes` se migran a `comprobantes_alimentario`.

## Despliegue

Backend y SISOC-Mobile deben publicarse coordinadamente. Aplicar migraciones
antes de desplegar la PWA y validar creación, envío, solicitud de faltante,
subsanación, exportación y edición con/sin permiso.
