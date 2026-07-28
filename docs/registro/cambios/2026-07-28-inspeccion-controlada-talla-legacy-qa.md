# Inspección controlada del dato legacy que bloquea QA

## Contexto

La migración `centrodeinfancia.0042_alter_nominacentroinfancia_talla` rechazó
un valor histórico no convertible en el registro 7 de
`NominaCentroInfancia.talla`. El rechazo es intencional: evita truncar o
reinterpretar datos de salud al transformar un campo de texto en decimal.

## Operación temporal

Se agrega un workflow manual, limitado al runner y Environment de QA, que:

- requiere la confirmación exacta `inspect-id-7`;
- verifica que el checkout local sea el SHA actual de `development`;
- consulta sólo la columna bloqueante mediante SQL parametrizado;
- informa únicamente su categoría (`null`, `blank`, `numeric`,
  `non_numeric` o `record_missing`) y nunca imprime el valor ni datos de la
  persona asociada.

El resultado permite seleccionar la corrección mínima y auditable sin exponer
PII ni ejecutar las migraciones desde el contenedor temporal.
