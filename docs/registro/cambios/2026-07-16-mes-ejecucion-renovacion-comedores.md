# Mes de ejecución durante la renovación de comedores

## Contexto

El mes de ejecución del listado y del legajo de comedores se obtenía del
`mes_convenio` del último expediente de pago. Cuando un comedor de Alimentar
Comunidad dejaba de aparecer en los lotes siguientes, el valor histórico seguía
visible aunque su estado ya hubiera cambiado a renovación o baja.

## Cambio funcional

`Comedor.mes_ejecucion` conserva el valor operativo vigente sin modificar el
`ExpedientePago.mes_convenio` histórico:

- comedor presente en el lote: mes de convenio informado (`1` a `6`);
- primera ausencia consecutiva: `-1`;
- segunda ausencia consecutiva: `-2`;
- tercera ausencia, o comedor que ya estaba inactivo: `null`.

La regla se aplica solamente a comedores del programa Alimentar Comunidad y
convive con la actualización de estados implementada en el flujo de importación.
El listado, los filtros avanzados y el resumen del legajo consumen el nuevo
campo operativo.

## Migración y compatibilidad

La migración inicializa `Comedor.mes_ejecucion` con el mes de convenio del
último expediente de cada comedor de Alimentar Comunidad. Los expedientes y
sus validadores de meses `1` a `6` no se modifican.

## Validación

- migraciones Django sin cambios pendientes;
- `manage.py check` sin errores;
- tests del flujo de importación, incluidas las transiciones a `-1`, `-2` y
  `null`.
