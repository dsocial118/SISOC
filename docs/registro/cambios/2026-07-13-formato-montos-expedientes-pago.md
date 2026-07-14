# Formato de montos en expedientes de pago

## Contexto

Los totales de expedientes de pago se mostraban con decimales o sin separadores de miles, lo que dificultaba la lectura de montos altos.

## Cambio

- Se agrega el filtro `monto_sin_decimales` para mostrar montos con separador de miles `.` y sin centavos.
- Se aplica el formato al campo `Total` del listado y detalle de expedientes de pago.
- Se aplica el formato a la columna `Monto Mensual` del detalle de expedientes de pago.
- Se aplica el formato a `Monto total de prestaciones` en el contenedor de mes de ejecucion del legajo de comedor.

## Validacion

- Tests unitarios del filtro y del item de listado de expedientes de pago.
- `djlint --check` sobre los templates modificados.
- `manage.py check`.
