# 2026-03-25 - Alineación de tests en comedores e importación

## Contexto
- `development` incorporó cambios recientes en dos contratos:
  - programa 2 sigue usando nómina por admisión; la nómina directa quedó acotada a programas 3/4.
  - la importación de Celiaquía ahora exige más campos obligatorios, incluidos datos del responsable.
- Quedaron tests viejos que seguían esperando el comportamiento anterior.

## Ajustes realizados
- Se actualizó el test del signal de admisiones para verificar la reasignación de nómina en programa 2.
- Se completó el fixture de importación de Celiaquía con los campos obligatorios vigentes para seguir validando `telefono` y `codigo_postal`.
- Se alineó la expectativa del mensaje de error de importación con el texto actual de validación.
- Se reemplazó un test legado de `ComedorService` por uno que cubre el helper actual de `ComedorDetailView` para redirigir el manejo histórico de relevamientos.

## Impacto
- No hay cambio funcional en la aplicación.
- La suite vuelve a validar el comportamiento vigente de `development`.
