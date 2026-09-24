# 2026-09-23 - Resumen de nómina del legajo sobre asistentes activos (#2507)

## Contexto
- El resumen de nómina del legajo mezclaba estados: "Asistentes" y "Género" contaban todos los
  registros, y el gráfico de rangos de edad dividía por el total, por lo que los registros en
  espera o de baja aparecían como "Sin dato".
- No se mostraba la cantidad de dados de baja.

## Cambios aplicados
- `comedores/services/comedor_service/impl.py`: el conteo por género cuenta solo activos; se agrega
  `baja` y `rangos` expone `espera` y `baja` (claves nuevas, aditivas).
- `comedores/views/comedor.py` (`_build_nomina_metrics`): "Asistentes" y los porcentajes del gráfico
  de edades se calculan sobre activos. "Sin dato" pasa a ser activos sin fecha de nacimiento.
- `comedores/templates/comedor/comedor_detail.html`: tarjeta "Dados de baja".

## Decisiones
- `cantidad_total` (total de registros) no cambia: la API de nómina lo usa como `count` de paginación.

## Riesgos y rollback
- Cambia la semántica de hombres/mujeres/X que devuelve `get_nomina_detail*` para todos sus
  llamadores (legajo y detalle de nómina); es el comportamiento pedido por el issue.
- Rollback: revertir el commit; no hay cambios de datos.
