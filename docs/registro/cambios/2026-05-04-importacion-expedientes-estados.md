# Importación de expedientes de pago y estados de comedores

## Contexto

El flujo `/importarexpedientes/listar` acepta el modelo nuevo de expediente de pago en `.xlsx`, que agrega `Mes de Convenio`. El dato se persiste en `ExpedientePago.mes_convenio` y queda visible solo en el detalle del expediente.

## Regla operativa

- La validación inicial del archivo solo registra filas válidas o errores; no modifica estados.
- La automatización corre al completar la importación del lote.
- Solo se actualizan comedores del programa `Alimentar comunidad` (`programa_id=2`).
- Lotes sin `Mes de Convenio` conservan la compatibilidad historica y no disparan cambios de estado.
- El valor de `Mes de Convenio` debe estar entre `1` y `6`.
- El borrado de un lote importado elimina expedientes y registros del lote, pero no revierte estados ya generados.

## Estados aplicados

- Meses `1`, `2` y `3`: `Activo / En ejecución / sin motivo`.
- Meses `4`, `5` y `6`: `Activo / En ejecución / En plazo de renovación`.
- Primera y segunda ausencia consecutiva: `Activo / En proceso - Renovación / sin motivo`.
- Tercera ausencia consecutiva o posterior: `Inactivo / Baja / No renovación (Comedor)`.
- Un comedor ya inactivo que aparece ausente permanece en `Inactivo / Baja / No renovación (Comedor)`.

## Alcance

La importación CSV existente sigue soportada. La automatización toma como inicio del conteo de ausencias el primer lote completado que tenga expedientes con `Mes de Convenio`.
