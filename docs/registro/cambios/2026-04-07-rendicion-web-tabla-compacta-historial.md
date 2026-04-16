# Rendicion web: tabla mas compacta e historial con observaciones

## Contexto

El detalle web de rendiciones todavia mantenia dos columnas iniciales
practicamente vacias despues de haber agrupado por categoria. Ademas, en el
historial de archivos observados el estado ocupaba un lugar visual poco util.

## Cambio realizado

- Se eliminaron las dos primeras columnas de la tabla (`Categoria` y
  `Condicion`) porque esa informacion ya se muestra en el encabezado del bloque.
- La tabla queda ahora en 5 columnas: `Archivo`, `Estado`, `Revision`, `Fecha`
  y `Acciones`.
- En el historial de `Comprobantes` y `Documentacion Extra`, la segunda columna
  ya no muestra estado: ahora muestra las observaciones del archivo historico.

## Validacion

- `docker compose exec django pytest tests/test_rendicioncuentasmensual_views_unit.py -q`
