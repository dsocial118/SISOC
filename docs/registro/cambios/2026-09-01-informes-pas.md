# Informes PAS

Fecha: 2026-09-01

## Alcance

- Se incorpora `PasInforme` como fotografía persistente del resultado generado.
- Los informes pueden filtrar el padrón vigente y su historial por fechas,
  estados, avisos, ubicación, identificadores y usuario responsable del cambio.
- La presencia de filtros históricos determina si el resultado representa
  titulares o cambios de estado.
- Se agregan listado, formulario de generación, previsualización JSON, detalle y
  descarga CSV.

## Decisiones

- La lógica de consulta, serialización y exportación vive en
  `pas/services/informe_service.py`; las vistas sólo coordinan formularios y
  respuestas HTTP.
- Cada informe conserva filtros, modo y filas serializadas para que su descarga
  posterior no cambie cuando se actualice el padrón.
- La exportación reutiliza la política CSV central, incluida la codificación con
  BOM para compatibilidad con planillas de cálculo.
- El PR no incorpora Panel avanzado, Formación, cruces, RENAPER ni accesos de
  navegación global. Esos componentes corresponden a entregas posteriores.
- La evolución de esquema se consolida en `0003_pasinforme`, dependiente de la
  migración `0002_pas_import_ddjj_tokens`.

## Validación

- Verificación de configuración Django y consistencia de migraciones.
- Formato Python con Black y templates con djLint.
- Pruebas cercanas del servicio de informes y de la política de exportación CSV.
