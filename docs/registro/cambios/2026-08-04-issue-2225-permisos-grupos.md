# 2026-08-04 - Issue 2225: cierre de permisos cruzados

## Cambio

- Historia Social Digital exige los permisos Django de lectura, alta, edición o baja según la operación; el buscador y la exportación requieren lectura.
- Los enlaces desde Nómina hacia el detalle de un ciudadano solo se muestran a quien tiene `ciudadanos.view_ciudadano`.
- Acompañamiento exige `acompanamientos.view_informacionrelevante` para listar, consultar detalle y usar el endpoint AJAX.
- El detalle y la restauración de hitos aplican el alcance de comedores del usuario. Restaurar hitos requiere el rol técnico y `acompanamientos.change_hitos`.

## Migración operativa

La migración `users.0042_revoke_acompanamiento_from_comedores_groups` revoca los permisos de Acompañamiento de `Comedores total` y `Comedores Visualización`, y concede la edición de hitos al grupo `Tecnico Comedor`.

No se revocan permisos directos ni de otros grupos: deben revisarse por separado si se detectan asignaciones excepcionales legítimas.
