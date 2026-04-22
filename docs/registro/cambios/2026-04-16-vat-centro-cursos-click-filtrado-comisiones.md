# VAT centro detalle: filtrado de comisiones por selección activa

## Fecha
- 2026-04-16

## Cambio
- En la pestaña `Cursos` del detalle de centro (`/vat/centros/<id>/`), las comisiones ya no se filtran al posar el cursor ni al tabular sobre una fila de curso.
- El filtrado por curso queda disponible únicamente mediante una selección activa del curso: click sobre la fila o activación por teclado (`Enter` / `Espacio`), además del selector `Curso` del bloque de filtros de comisiones.

## Motivación
- Evitar que la exploración visual del listado dispare cambios automáticos en la tabla de comisiones.
- Mantener una interacción predecible y alineada con los filtros explícitos del panel.

## Alcance técnico
- Se removió el estado transitorio de `preview` usado por `hover`/`focus` en el script del detalle de centro.
- Se conservó el bloqueo/desbloqueo explícito del curso seleccionado y la sincronización con el selector de filtros.
- Se agregó una regresión de render para asegurar que el detalle no vuelva a registrar handlers de `mouseenter`/`focus` para este filtro.

## Validación
- `pytest VAT/tests.py -k "centro_detail_difiere_panel_cursos_hasta_abrir_solapa or centro_cursos_panel_renderiza_marcadores_para_filtrar_comisiones_por_curso"`
