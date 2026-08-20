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
- Una solicitud de documento faltante se registra por categoría, aun cuando la
  categoría ya tenga archivos. La PWA habilita esa categoría durante la
  subsanación y la solicitud se cierra al adjuntar un archivo nuevo.
- Los documentos previamente validados conservan su estado al reenviar una
  subsanación.

## Contrato de carga

- Convenios admitidos: `P01`, `P02`, `P03`.
- Números de rendición admitidos: `1` a `6`.
- Inicio y fin deben pertenecer al mismo mes y no se admiten períodos anteriores
  al último ya gestionado para el mismo convenio y proyecto.
- Formulario I, ambos Formulario V, Formulario VI y Extracto Bancario admiten
  múltiples archivos. Los comprobantes se separan entre Prestación Alimentaria
  y SIPH.

## Despliegue y validación

Aplicar `rendicioncuentasmensual.0017` antes de usar las solicitudes de faltantes.
Validar una rendición nueva con proyecto, una histórica con fallback, una
subsanación de Territorial y otra de Auditoría antes de promover a producción.

## Referencias

- `rendicioncuentasmensual/services.py`
- `organizaciones/views.py`
- `docs/registro/cambios/2026-08-10-fixes-admisiones-pwa-rendiciones.md`
- `docs/registro/cambios/2026-08-12-correcciones-issues-reabiertos.md`
