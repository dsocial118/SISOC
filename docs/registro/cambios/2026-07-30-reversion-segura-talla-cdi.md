# 2026-07-30 - Reversión segura de la conversión de talla CDI

## Contexto

El PR #2144 convirtió `NominaCentroInfancia.talla` de texto a `DecimalField(5,1)`
y agregó la migración `centrodeinfancia.0042_alter_nominacentroinfancia_talla`.
El despliegue de producción se detuvo antes del cambio de esquema al encontrar
valores históricos de texto no convertibles. No se modificaron esas filas.

## Decisión

- `talla` vuelve a ser `CharField(max_length=50)` y deja de ser obligatoria o
  validada como medida numérica en el formulario de destinatarios CDI.
- La migración 0042 no ejecuta operaciones de base de datos. Conserva sólo su
  estado histórico decimal para que la nueva 0043 pueda restaurar físicamente la
  columna a texto en cualquier entorno donde 0042 sí hubiera sido aplicada.
- Se conservan las validaciones y obligatoriedad de `peso`, `longitud_acostado`
  y `perimetro_cefalico`; no forman parte del incidente.
- El workflow de deploy ya no expone la acción que podía asignar `NULL` a las
  tallas legacy; sólo conserva la inspección de lectura.

## Compatibilidad y operación

En producción, donde 0042 se detuvo antes de alterar la columna, 0042 no toca
datos y 0043 vuelve a declarar la misma columna de texto. En un entorno que ya
hubiera aplicado 0042, 0043 convierte la columna decimal a texto sin descartar
valores.

No se deben ejecutar acciones de reparación de datos para este incidente. Un
retroceso futuro desde 0043 hacia decimal requiere preflight de valores y backup:
los textos legacy podrían no ser convertibles.
