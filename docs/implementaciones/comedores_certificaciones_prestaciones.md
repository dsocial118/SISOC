# Certificaciones mensuales de prestaciones

## Flujo

La conformidad mensual genera un PDF de certificación para afirmaciones y no
conformidades, usando una de cuatro plantillas según el resultado y si opera el
usuario principal o un subusuario. El historial web y la PWA muestran el estado
y permiten descargar el archivo generado.

## Fallback sin fuente

Si falta informe técnico o convenio, se usa una fuente explícita con
prestaciones en cero. El PDF incluye la leyenda **“Datos de prestaciones no
disponibles.”**; no inventa prestaciones ni atribuye datos inexistentes.

Los registros históricos sin archivo se mantienen visibles como no disponibles
para descarga. Para altas nuevas, una falla al generar o guardar el PDF revierte
la conformidad: no queda una certificación parcial.

## Operación y rollback

Verificar en cada ambiente las cuatro plantillas versionadas bajo
`pwa/files/varios/` y una descarga con fuente y otra con fallback. Revertir la
aplicación restaura el comportamiento previo para altas nuevas; no modifica los
archivos ni registros ya creados.

## Referencias

- `comedores/services/certificacion_prestaciones_service.py`
- `comedores/api_views.py`
- `docs/registro/cambios/2026-08-13-certificaciones-prestaciones-sin-fuente.md`
