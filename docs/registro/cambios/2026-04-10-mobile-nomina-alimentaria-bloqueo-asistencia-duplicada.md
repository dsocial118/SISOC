# Mobile — bloqueo de asistencia duplicada por período en nómina alimentaria

**Fecha:** 2026-04-10
**Archivo tocado:**
- `mobile/src/features/home/SpaceNominaAlimentariaAttendancePage.tsx`

## Comportamiento

Al cargar la nómina, se calculan los `lockedIds`: IDs de personas que ya tienen
`asistencia_mes_actual !== null` (asistencia registrada en el período actual).

- Las personas con asistencia ya registrada muestran un badge "Ya registrada",
  tienen el checkbox deshabilitado y no pueden ser modificadas.
- Las personas sin asistencia pueden marcarse/desmarcarse normalmente.
- Los botones "Seleccionar todo" / "Deseleccionar todo" operan solo sobre los no bloqueados.
- El aviso informativo indica cuántas personas ya tienen asistencia registrada.
- El botón "Guardar asistencia" sigue activo para registrar el resto.

## Por qué solo frontend

El backend ya maneja la unicidad con `get_or_create` por
`(nomina_id, periodicidad_mensual, periodo_referencia)`. El riesgo real era
el borrado accidental de registros existentes al re-enviar con personas deseleccionadas.
Bloquear en el cliente los ya registrados es suficiente y no invasivo.
