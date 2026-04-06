# Fix migrate admisiones documentacion.tipo

## Qué se corrigió

- Se ajustó la migración `admisiones/0012_remove_documentacion_tipo_admision_archivo_convenio_and_more.py` para que elimine `Documentacion.tipo` solo si la columna `tipo_id` todavía existe en MySQL.

## Motivo

- En algunas bases el estado de migraciones y el esquema físico quedaron desfasados, provocando `OperationalError (1091): Can't DROP 'tipo_id'` durante `migrate`.

## Criterio operativo

- El estado de Django sigue removiendo el campo.
- La operación SQL real ahora es tolerante si la columna o su FK ya fueron eliminadas antes.
