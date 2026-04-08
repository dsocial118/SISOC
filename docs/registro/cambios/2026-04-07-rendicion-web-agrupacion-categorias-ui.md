# Rendicion web: agrupacion visual por tipo de archivo

## Contexto

En el detalle web de rendiciones, todos los documentos se mostraban dentro de
una sola tabla con repeticion de categoria por fila. Eso hacia mas dificil leer
rapido cada bloque de archivos y distinguir el tipo documental al que
pertenecian.

## Cambio realizado

- Se agrego un encabezado visual por cada categoria de documentacion dentro de
  la tabla.
- Cada bloque ahora muestra:
  - nombre de la categoria,
  - si es obligatoria u opcional,
  - cantidad de archivos del bloque.
- Las filas internas ya no repiten visualmente la categoria en cada documento,
  para priorizar el nombre del archivo, el estado y la revision.

## Validacion

- `docker compose exec django pytest tests/test_rendicioncuentasmensual_views_unit.py -q`
