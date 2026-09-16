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

## Etapas, permisos y estados visibles

El flujo tiene cinco etapas: `Carga de documentación`, `Revisión Territorial`,
`Revisión para Carga`, `Auditoría` y `Regularización`. Las acciones se
autorizan con permisos Django configurables por grupo:

- `manage_territorial_stage`
- `manage_auditoria_review_stage`
- `manage_auditoria_stage`
- `manage_regularizacion_stage`

El permiso de etapa habilita listado, detalle, descarga y acciones de esa
etapa, pero no concede por sí solo edición de datos generales, creación o
eliminación. La interfaz y los POST aplican la misma comprobación de permisos.

`Revisión para Carga` es solamente la denominación visible de la etapa cuyo
valor persistido sigue siendo `revision_auditoria` (issue #2377). La constante
`ETAPA_REVISION_AUDITORIA`, los nombres de permisos y los `value` de los filtros
no cambiaron. No debe confundirse con la etapa independiente `Auditoría`
(`auditoria`). Cualquier consumidor —la PWA incluida— tiene que distinguir el
estado por `etapa_proceso` + `subestado_proceso`, nunca por la etiqueta.

El filtro `Estado` combina `etapa_proceso` y `subestado_proceso`, y refleja el
texto visible de la columna. `Estado general` mantiene el filtro histórico.
`Etapa` incluye las cinco opciones del modelo. Los datos generales requieren
fecha de inicio y fin del período, aunque esos campos sigan siendo anulables
para preservar registros históricos.

Una solicitud de documento faltante puede acumularse durante la revisión. La
etapa deriva a subsanación al finalizar la revisión si queda alguna solicitud
activa; al adjuntar un archivo nuevo se cierra la solicitud de su categoría.
Las observaciones quedan visibles debajo de la categoría solicitada.

## Contrato de carga

- Convenios admitidos: `P01`, `P02`, `P03`.
- Números de rendición admitidos: `1` a `6`.
- El número debe ser además **el siguiente de la secuencia** dentro del mismo
  proyecto y convenio: si el último es 2, el único valor aceptado es 3. La regla
  vive en `RendicionCuentaMensualService` y la aplican por igual el alta y la
  edición, en web y en API; no se delega en la PWA. Participan los borradores y
  quedan afuera las bajas lógicas, así que dar de baja una rendición libera su
  número. Editar sin cambiar el número no revalida la secuencia.
- La asignación del número se serializa con `select_for_update()` sobre la fila
  ancla del scope (proyecto, o comedor en el camino legado) dentro de la misma
  transacción que escribe, para que dos altas concurrentes no tomen el mismo.
- No se admiten períodos anteriores al último ya gestionado para el mismo
  convenio y proyecto, ni solapamientos.
- Inicio y fin deben pertenecer al mismo mes, **salvo en
  `Abordaje Comunitario - Línea Secos`**, donde el fin puede llegar hasta el
  último día del tercer mes calendario contado desde el mes de inicio
  (03/09 → 30/11). El cálculo usa el calendario real, no una cantidad fija de
  días. El error se devuelve en el campo `periodo_fin`.
- Las validaciones acumulan todos los errores y se devuelven identificados por
  campo (`convenio`, `numero_rendicion`, `periodo_inicio`, `periodo_fin`,
  `periodo`), para que la PWA los pueda mostrar junto al campo correspondiente.
- Formulario I, ambos Formulario V, Formulario VI y Extracto Bancario admiten
  múltiples archivos. Los comprobantes se separan entre Prestación Alimentaria
  y SIPH, y se muestran como `Facturas y Tickets Prestación Alimentaria` y
  `Facturas y Tickets SIPH` (cambio de etiqueta; los códigos
  `comprobantes_alimentario` y `comprobantes_siph` no cambian).
- El catálogo documental depende de la línea programática:
  `Planilla de Seguros` no se pide en `Línea Secos` y sí en `Línea Tradicional`.
  Web y API lo resuelven con `RendicionCuentaMensualService.obtener_categorias_visibles`,
  que además sigue mostrando las categorías desactivadas para la línea cuando la
  rendición ya tiene documentos históricos cargados en ellas.

## Despliegue y validación

Aplicar `rendicioncuentasmensual.0017`, luego
`rendicioncuentasmensual.0018` y finalmente
`rendicioncuentasmensual.0019_reconciliar_comprobantes_legacy` antes de usar
solicitudes de faltantes o permisos por etapa. La última migración reconcilia
la categoría legacy de comprobantes, también en registros con baja lógica.
Antes de aplicarla en producción, tomar un backup recuperable y detener las
instancias que aún puedan escribir `comprobantes`; validar después que no queden
filas con esa categoría. Configurar los grupos desde Usuarios > Grupos y
asignar únicamente los permisos de las etapas que correspondan.

Para una prueba local aislada, usar
`python manage.py seed_rendicion_stage_examples --comedor-id <id>`. El comando
solicita de forma interactiva una contraseña de al menos 12 caracteres, crea
cuatro usuarios/grupos QA y cuatro rendiciones en el comedor indicado, y es
idempotente. No ejecutarlo sobre datos productivos: está destinado a QA local
o de entorno controlado.
Validar una rendición nueva con proyecto, una histórica con fallback, una
subsanación de Territorial y otra de Auditoría antes de promover a producción.

## Referencias

- `rendicioncuentasmensual/services.py`
- `organizaciones/views.py`
- `docs/registro/cambios/2026-08-10-fixes-admisiones-pwa-rendiciones.md`
- `docs/registro/cambios/2026-08-12-correcciones-issues-reabiertos.md`
