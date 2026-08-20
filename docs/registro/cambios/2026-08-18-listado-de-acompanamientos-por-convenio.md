# Listado de acompañamientos por convenio

## Fecha

2026-08-18

## Problema

El requerimiento pedía que todos los acompañamientos persistieran en la pantalla
de acompañamientos "a fin de poder revisar el histórico", con la etiqueta
"Cerrado" o "Finalizado" según correspondiera.

La pantalla no lo permitía por dos motivos:

1. **Excluía lo inactivo.** `obtener_comedores_acompanamiento` exigía
   `activa=True` en el `Exists`, en el `Prefetch` y en los `Subquery` de
   anotación. Un comedor cuya admisión había sido cerrada desaparecía del
   listado.
2. **El grano era el comedor, no el acompañamiento.** La grilla tenía una fila
   por `Comedor`, con las columnas resueltas a partir de la admisión activa más
   reciente. Un comedor con tres convenios era una sola fila, así que no había
   dónde poner una etiqueta por acompañamiento.

## Decisión

Producto confirmó **una fila por acompañamiento**. La razón es la que declara el
propio requerimiento: con una fila por comedor, un convenio cerrado que convive
con uno vigente nunca se ve, y el histórico sigue sin poder revisarse. Además el
ticket pide que la pantalla se comporte "de la misma manera" que el selector de
convenios, que lista cada convenio con su etiqueta.

## Cambio

- `AcompanamientoService.obtener_comedores_acompanamiento` →
  `obtener_acompanamientos`. La base del queryset pasa de `Comedor` a `Admision`
  filtrada por `enviado_acompaniamiento=True`, **sin** filtro por `activa`.
- Anotación `estado_acompanamiento` con los estados de `Acompanamiento`:
  `activo`, `cerrado`, `finalizado`.
- `preparar_datos_tabla_comedores` → `preparar_datos_tabla_acompanamientos`, con
  dos columnas nuevas: **Convenio** (que es lo que ahora distingue una fila de
  otra) y **Estado del acompañamiento** (el badge).
- Filtro nuevo "Estado del acompañamiento" en `filter_config`, y el resto de los
  campos remapeados a la nueva base (`comedor__nombre`, `estado_admision`, etc.).
- `ComedoresAcompanamientoListView` → `AcompanamientosListView`. Los nombres de
  URL no cambiaron, así que no se rompe ningún `reverse` ni link del sidebar.
- Export CSV y vista AJAX alineados al nuevo grano.

## Por qué la base es Admision y no Acompanamiento

Sería más directo consultar `Acompanamiento`, que es literalmente la entidad
listada. Se usa `Admision` porque el backfill de la migración `0008` quedó
marcado como aplicado en QA y producción con una versión anterior, así que puede
haber admisiones enviadas a acompañamiento **sin** su fila de `Acompanamiento`.
Con `Acompanamiento` como base esas filas desaparecerían del listado; con
`Admision` el resultado es un superconjunto del listado anterior y no puede
perderse ninguna fila. La ausencia de `Acompanamiento` se interpreta como no
finalizado.

## Precedencia de estados

Si un acompañamiento finalizado recibe después un forzar cierre, la etiqueta que
se muestra es **Cerrado**: es el hecho posterior y el más definitivo. Es la misma
precedencia que ya usaban los selectores de convenio.

## Arreglos incidentales

- **Export CSV con columnas vacías.** `CSVExportMixin.resolve_field` navega los
  paths con puntos, pero el mapa de columnas usaba lookups del ORM
  (`organizacion__nombre`). Esas celdas se exportaban vacías en silencio. Ahora
  usan notación con puntos (`comedor.organizacion.nombre`) y hay un test que lo
  cubre.
- **Choices de filtros todo-o-nada.** `get_filters_ui_config` armaba las choices
  estáticas y las de base de datos dentro del mismo `try`, así que una falla al
  consultar provincias o duplas se llevaba puestas también las estáticas. Ahora
  las estáticas se resuelven aparte.

## Preferencias de columnas

La tabla usa una clave nueva (`acompanamientos_list` en lugar de
`acompanamientos_comedores_list`) porque cambió de forma: con la clave anterior,
las preferencias guardadas apuntarían a columnas que ya no existen. Los usuarios
arrancan con el set de columnas por defecto.

## Validación

- `tests/test_acompanamientos_list_filters_db.py`: reescrito para el nuevo grano.
  Cubre que dos admisiones den dos filas, que cerrados y finalizados persistan
  con su etiqueta, el filtro por estado del acompañamiento, que cada fila apunte
  a su propio convenio, y las columnas relacionadas del export.
- `tests/test_acompanamientos_filter_config_unit.py` y
  `tests/test_acompanamiento_service_helpers_unit.py` actualizados.
- Selección `acompanamiento or comedor or intervencion or admision`: 574
  aprobados. `test_dashboard_uses_public_comedores_projection` falla también en
  árbol limpio; es previo y ajeno.

## Pendiente

Este cambio cierra el requerimiento del listado. Queda fuera el evolutivo de
Expedientes de Pago, que se trabaja aparte.
