# Timeout al importar estados de comedores

## Contexto

La importacion de expedientes actualiza estados de comedores mediante
`registrar_cambio_estado`. Ese flujo crea un `EstadoHistorial` y actualiza el
puntero `Comedor.ultimo_estado`.

Antes del cambio, esa actualizacion usaba `comedor.save(update_fields=["ultimo_estado"])`.
Aunque solo cambiaba el estado operativo, Django disparaba los `pre_save` de
`Comedor`, incluyendo la sincronizacion completa hacia GESTIONAR y la auditoria
general del modelo.

## Cambio

`registrar_cambio_estado` ahora actualiza el puntero `ultimo_estado` con
`QuerySet.update()` dentro de la misma transaccion.

Esto mantiene el historial de estado como fuente del cambio y evita tratar el
puntero denormalizado como una edicion completa del comedor.

## Impacto

- La importacion sigue creando `EstadoHistorial` y dejando actualizado
  `Comedor.ultimo_estado`.
- Los cambios de estado no arman payload completo de comedor hacia GESTIONAR.
- Se reducen consultas innecesarias a relaciones como `referente` durante lotes
  grandes.
- La auditoria funcional del estado queda en `EstadoHistorial`.

## Validacion esperada

Ejecutar el test de regresion:

```bash
pytest importarexpediente/tests/test_import_flow.py::test_import_estado_update_does_not_sync_comedor_payload -q
```
