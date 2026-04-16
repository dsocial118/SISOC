# Mobile: hub inicial con compatibilidad para organizaciones sin `tipo_asociacion` consistente

Fecha: 2026-03-30

## Qué cambió

- El hub inicial mobile ya no pierde organizaciones cuando los espacios vienen con datos de organización válidos pero sin `tipo_asociacion='organizacion'` explícito.

## Implementación

- La lógica de agrupado del home ahora trata como organización a cualquier espacio que tenga `organizacion_id` y `organizacion__nombre`, salvo que el backend marque explícitamente `tipo_asociacion='espacio'`.
- Los accesos directos siguen mostrándose como extras sólo cuando son realmente de tipo espacio o no tienen organización asociada.

## Validación

- `npm run build` en `mobile/`
