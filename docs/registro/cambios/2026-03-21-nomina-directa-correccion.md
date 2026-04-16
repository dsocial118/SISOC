# 2026-03-21 - Corrección de nómina directa

## Contexto
- El PR `#1332` agrega el flujo de nómina directa para programas 3/4.
- Durante la revisión aparecieron dos regresiones: la confirmación de baja directa no resolvía el cancel URL correcto y las vistas directas no estaban cerradas por programa.

## Cambios aplicados
- Se incorporó el helper `_get_comedor_directo_or_404(...)` para validar que la nómina directa solo aplique a comedores de programa 3/4.
- Se reutilizó ese helper en `NominaDirectaDetailView`, `NominaDirectaCreateView` y `NominaDirectaDeleteView`.
- Se corrigió `templates/comedor/nomina_confirm_delete.html` para resolver el cancel URL directo cuando `admision_pk` no existe.
- Se agregaron tests de regresión para:
  - `404` en nómina directa de programa 2.
  - render correcto de la confirmación de baja directa con retorno a la vista directa.

## Motivo
- El fix evita que la nueva superficie de nómina directa quede expuesta a comedores que no corresponden y restablece la navegación correcta del flujo de baja.

## Impacto esperado
- Los comedores de programa 2 no podrán usar el flujo directo.
- La confirmación de borrado de nómina directa vuelve a mostrar un enlace de cancelación válido.
