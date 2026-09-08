# Etiqueta CARITAS en comedores

## Cambio funcional

- Se incorpora `¿Es CARITAS?` como dato obligatorio en las altas y ediciones web de comedores.
- Cuando el valor es `Sí`, el legajo del comedor y la tabla de comedores asociados de su organización muestran el badge `CARITAS`.
- La PWA no expone este dato en el resumen de domicilio, igual que el dato de judicialización.

## Datos existentes

La columna admite `NULL` para conservar la falta de definición histórica sin convertirla incorrectamente en `No`. El formulario obliga a seleccionar `Sí` o `No` al crear o volver a guardar un legajo.
