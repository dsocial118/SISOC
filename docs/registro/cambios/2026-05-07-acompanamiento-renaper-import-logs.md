# 2026-05-07 - Importacion de acompanamiento y logs RENAPER

## Contexto

Se detectaron dos errores operativos en logs:

1. `AcompanamientoService.importar_datos_desde_admision` intentaba leer
   `admision.prestaciones`, pero `Admision` no expone esa relacion.
2. La consulta RENAPER registraba como `ERROR` valores no numericos esperables
   en campos numericos de domicilio, por ejemplo `-` o `S/N`.

## Que cambio

- `acompanamientos/acompanamiento_service.py`
  - La importacion de prestaciones ahora toma el `InformeTecnico` mas reciente
    de la admision y deriva una fila por dia con prestaciones aprobadas.
  - Se mantiene el modelo `Prestacion` actual: guarda banderas por tipo de
    comida, no cantidades.
- `centrodefamilia/services/consulta_renaper/impl.py`
- `VAT/services/consulta_renaper/impl.py`
  - Los placeholders no numericos conocidos se normalizan a `None` sin
    emitir `logger.error`.

## Decision

La fuente real de las prestaciones aprobadas para acompaniamiento es
`InformeTecnico`, no una relacion inexistente en `Admision`.

Para RENAPER, `-`, `S/N` y equivalentes representan ausencia de dato, no un
fallo del servicio externo.

## Validacion

- Tests unitarios focalizados de acompanamiento y RENAPER.
- `black --check` sobre los archivos modificados.
- `git diff --check`.
