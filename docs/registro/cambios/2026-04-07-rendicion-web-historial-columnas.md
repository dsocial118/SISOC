# Rendicion web: historial con columnas utiles

## Contexto

En el historial de `Comprobantes` y `Documentacion Extra` habia una fila
extra de separacion y ademas se estaba reutilizando la columna `Revision` para
acciones que no aportaban valor en documentos historicos.

## Cambio realizado

- Se elimino la fila `Archivos anteriores observados`.
- Los documentos historicos de esas categorias ahora se muestran en una sola
  fila cada uno con estas columnas:
  - nombre de archivo,
  - estado,
  - observaciones con formato `Obs: ...`,
  - fecha,
  - accion `Ver`.

## Validacion

- `docker compose exec django pytest tests/test_rendicioncuentasmensual_views_unit.py -q`
