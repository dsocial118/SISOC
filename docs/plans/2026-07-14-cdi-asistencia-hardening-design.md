# Hardening de asistencia de trabajadores CDI

Estado: aprobado para preparar antes del deploy productivo del 2026-07-14.

## Riesgos a resolver

- Una fecha POST invalida se convertia silenciosamente en la fecha actual.
- Cualquier marca distinta de `1` se guardaba como ausencia.
- El lote ejecutaba escrituras independientes sin una transaccion comun.
- `observaciones` se reenviaba en un input oculto y no era editable en la UI.

## Diseno

La vista conserva scope, permisos y redirect existentes, pero delega la escritura
en `AsistenciaTrabajadorService`:

1. fecha ausente usa hoy para compatibilidad; fecha presente debe ser
   `AAAA-MM-DD` valida;
2. solo se aceptan las marcas `0` y `1`;
3. se valida el lote completo antes de escribir;
4. todos los `update_or_create` corren dentro de una unica
   `transaction.atomic()`;
5. un trabajador sin marcar sigue sin generar registro;
6. observaciones se muestra como input editable por fila.

Los errores de validacion muestran un mensaje y no escriben datos. Una excepcion
de base de datos se propaga, pero la transaccion revierte el lote completo para
que el error operativo sea visible y no deje una carga parcial.

## Compatibilidad y rollback

No cambia modelo, migracion, URL, permiso ni schema. El rollback es revertir el
PR; los registros ya guardados siguen siendo compatibles con la version previa.

## Validacion

- regresiones existentes de asistencia;
- fecha invalida sin escrituras;
- marca invalida despues de una marca valida sin escrituras;
- falla simulada en la segunda escritura con rollback de la primera;
- observaciones existentes visibles y editables en el HTML.
