# 2026-03-25 - Programas con nómina independiente

## Contexto
- Los programas 3 y 4 no usan admisiones para su nómina.
- La información de programa vive en `comedores/fixtures/programas.json` y se carga vía `load_fixtures`.

## Cambios aplicados
- Se agregó `Programas.usa_admision_para_nomina` como fuente de verdad del flujo.
- Se backfilleó el valor en migración para dejar `False` en los programas 3/4.
- Se actualizaron los fixtures de programas con el nuevo booleano.
- Se centralizó la regla en un helper de `comedores.utils` para evitar hardcodear IDs.
- Se bloquearon las rutas de creación de admisiones para comedores que usan nómina directa.
- El detalle del comedor y los flujos de nómina directa ahora respetan ese flag.
- `load_fixtures` suma `--overwrite` como alias explícito de `--force` para reaplicar fixtures existentes.

## Motivo
- Evitar inconsistencias entre fixtures, señales y vistas cuando un comedor no tiene admisiones.

## Impacto esperado
- Los programas 3 y 4 siguen operando con nómina directa.
- El resto de los programas mantiene el flujo por admisión.
- La carga de fixtures puede reaplicar datos existentes sin borrar filas.
