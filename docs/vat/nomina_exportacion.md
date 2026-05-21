# Exportacion de nominas VAT

## Objetivo

Consolidar las reglas vigentes para exportar nominas VAT evitando filas incompletas cuando la fuente principal no trae todos los datos.

## Regla de datos

La exportacion prioriza los datos estructurados de la nomina. Cuando faltan valores necesarios para completar la fila, usa observaciones como fuente complementaria controlada.

## Comportamiento esperado

- No se deben perder filas por ausencia de datos no criticos si las observaciones contienen la informacion recuperable.
- El fallback desde observaciones debe completar la exportacion sin modificar la entidad fuente.
- La exportacion debe seguir respetando filtros, permisos y alcance territorial del usuario.
- Los cambios de formato de exportacion deben cubrirse con tests de servicio o vista antes de tocar templates.

## Riesgos

- Las observaciones no son un contrato tan fuerte como campos estructurados; cualquier parseo nuevo debe ser defensivo.
- Si una columna pasa a ser dato obligatorio de negocio, corresponde modelarla o poblarla en origen en lugar de ampliar indefinidamente el fallback textual.
