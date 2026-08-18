# Rendiciones mensuales y proyectos de organizaciones

## Asociación de proyecto

`RendicionCuentaMensual.proyecto` es la relación principal con
`ProyectoOrganizacion`. Para registros históricos se conserva el fallback por
`comedor.codigo_de_proyecto`; los listados, notificaciones y el detalle no
deben excluir datos legados cuando esa relación nueva todavía sea nula.

La PWA ofrece los proyectos activos de la organización y persiste el proyecto
seleccionado en la rendición. La publicación de SISOC y SISOC-Mobile debe ser
coordinada cuando cambie este contrato.

## Revisión y subsanaciones

- Validar u observar documentos no cambia por sí solo el estado global: la
  etapa se resuelve al finalizar la revisión.
- Territorial mantiene la rendición `En revisión` al derivarla a Auditoría.
  Solo el cierre satisfactorio de Auditoría finaliza la presentación.
- Una subsanación conserva la etapa que la originó. Al reanudar Auditoría se
  preservan documentos ya validados; solo el primer inicio restablece los
  documentos heredados desde Territorial.
- El cierre administrativo de Auditoría usa un único formulario con monto,
  acta, resultado y observaciones condicionales.

## Despliegue y validación

Aplicar `rendicioncuentasmensual.0016` antes de usar la asociación directa.
Validar una rendición nueva con proyecto, una histórica con fallback, una
subsanación de Territorial y otra de Auditoría antes de promover a producción.

## Referencias

- `rendicioncuentasmensual/services.py`
- `organizaciones/views.py`
- `docs/registro/cambios/2026-08-10-fixes-admisiones-pwa-rendiciones.md`
- `docs/registro/cambios/2026-08-12-correcciones-issues-reabiertos.md`
