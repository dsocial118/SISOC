# Celiaquia: borrado del responsable en registros erróneos

## Fecha

2026-03-31

## Contexto

En la edición de registros erróneos de importación de celiaquía, si se cargaba un dato
parcial del responsable se exigía completar el resto del bloque, lo cual es correcto.

El problema era que, si luego se borraba ese único dato, el backend conservaba valores
previos del bloque responsable durante la consolidación del payload y seguía
considerando que existían datos del responsable.

## Cambio realizado

- Se ajustó la consolidación de `datos_raw` en `celiaquia/views/expediente.py`.
- Si la actualización toca campos del responsable y, luego de consolidar, el bloque
  responsable queda completamente vacío, se elimina todo el bloque responsable del
  registro.
- Se agregó test de regresión para asegurar que borrar el último dato del responsable
  deja de exigir la completitud del bloque.

## Impacto esperado

- Si el usuario carga al menos un dato del responsable, se sigue exigiendo completar
  los obligatorios.
- Si el usuario borra el único dato cargado del responsable, el sistema deja de pedir
  completar ese bloque.
- No cambia el comportamiento de merge para otros campos omitidos del registro erróneo.
