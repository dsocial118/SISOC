# VPSL: catálogo de vehículos en base de datos

## Contexto

El selector múltiple de vehículos de una jornada usaba cuatro opciones
definidas en código. Esto impedía modificar la oferta sin desplegar una nueva
versión de la aplicación.

## Cambios

- Se creó el catálogo `VehiculoVPSL`, con ID automático, nombre, orden y estado
  activo.
- El formulario de jornada obtiene sus opciones activas desde este catálogo.
- Al editar una jornada se conservan visibles sus selecciones aunque un
  vehículo haya sido desactivado posteriormente.
- Los nombres mostrados en jornadas y exportaciones se resuelven desde el
  catálogo, por lo que un cambio de nombre se refleja automáticamente.
- El catálogo queda disponible en Django Admin para altas, modificaciones,
  ordenamiento y desactivación.
- Un vehículo ya asociado a jornadas no se puede borrar físicamente desde el
  Admin, para no alterar datos históricos; se lo desactiva para retirarlo de
  nuevas selecciones. Los vehículos todavía no usados sí se pueden eliminar.
- Las jornadas y los vehículos se vinculan mediante una relación Many-to-Many
  real. El formulario envía los ID administrados por Django y no usa códigos
  paralelos.
- La migración crea `Vehiculo 1`, `Vehiculo 2`, `Vehiculo 3` y `Vehiculo 4`
  como datos iniciales.

## Migración y compatibilidad

La migración consolidada `0015_vpsl_ubicacion_vehiculos_graduaciones` copia la
selección singular histórica a la tabla intermedia Many-to-Many y luego retira
el campo anterior.
