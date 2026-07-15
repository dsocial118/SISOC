# CDI: asistencia del personal (Trabajadores)

## Fecha
2026-07-13

## Objetivo
Permitir registrar la asistencia del personal del centro (modelo
`Trabajador`) en el módulo Centro de Desarrollo Infantil, tomando como
referencia la funcionalidad de asistencia de VAT.

## Diferencia de dominio con VAT
VAT toma asistencia por **sesión** (una clase con fecha, autogenerada desde el
horario de la comisión → `SesionComision` + `AsistenciaSesion`). El personal
del CDI no tiene sesiones, así que la unidad de asistencia acá es **por fecha
(día)**: un registro por `(trabajador, fecha)`.

## Alcance de esta versión
- Tomar asistencia del personal de un centro para una fecha (por defecto hoy).
- Ver/editar el historial: un selector de fecha recarga lo ya registrado para
  ese día (editable).
- Estados: presente / ausente (booleano) + `observaciones`, igual que VAT.
- No incluye reporte/exportación ni estados extra (licencia/justificada).

## Cambios
- **Modelo** `AsistenciaTrabajador` (`centrodeinfancia/models.py`): FK a
  `Trabajador` (`related_name="asistencias"`), `fecha`, `presente`,
  `observaciones`, `registrado_por` (User, PROTECT), `fecha_registro`.
  `unique_together = ("trabajador", "fecha")` + índice `(fecha, presente)`.
  Migración `0036_asistenciatrabajador`.
- **Vista** `AsistenciaTrabajadorCentroView` (`TemplateView`,
  `centrodeinfancia/views.py`): calcada del patrón de
  `VAT.AsistenciaSesionView`. GET arma las filas del personal mapeando las
  asistencias existentes de la fecha y calcula métricas
  (presentes/ausentes/sin marcar); POST hace `update_or_create` por trabajador
  y redirige a la misma página con `?fecha=` para ver lo guardado. Un
  trabajador **sin marcar no genera registro** (a diferencia de VAT, que fuerza
  presente=False). Reutiliza `_get_centro_cdi_scoped_or_404` (scope
  territorial) y `_parse_fecha_renaper` (parseo de fecha con fallback a
  `timezone.localdate()`).
- **URL** `centrodeinfancia/<int:pk>/trabajadores/asistencia/`
  (`name="centrodeinfancia_trabajadores_asistencia"`), gateada por
  `centrodeinfancia.change_centrodeinfancia` — la misma llave que ya gobierna
  el alta/edición de trabajadores, para que funcione de inmediato con los roles
  existentes sin migrar permisos de grupos. El modelo igual expone sus permisos
  propios (`*_asistenciatrabajador`) para uso futuro.
- **Template** `trabajador_asistencia.html`: en el lenguaje visual del
  rediseño (`.cdf-page cdi-page` + `cdf.css`/`centrodeinfancia.css`). Hero,
  selector de fecha (GET), tarjetas de métricas, tabla con radios
  presente/ausente reutilizando `.cdf-mark` / `.cdf-check--present/absent`
  (estilos que ya existían en `cdf.css`, portados de VAT), "marcar todos",
  métricas en vivo y paginación client-side (JS adaptado de
  `asistencia_sesion.html`).
- **Detalle** (`centrodeinfancia_detail.html`): botón "Tomar asistencia" en la
  card Trabajadores, junto a "Agregar trabajador", gateado por
  `puede_editar_trabajadores`.

## Validación
- `makemigrations` + `migrate` en la MySQL local del compose.
- `pytest centrodeinfancia/tests/test_asistencia_trabajador.py` (7) +
  `test_trabajadores_views.py` (7) → 14 pasan.
- `djlint --check` sobre `trabajador_asistencia.html` y
  `centrodeinfancia_detail.html`.
- Smoke con test client: botón presente en el detalle; GET default (fecha hoy,
  12 filas), POST crea registro y redirige con `?fecha=`, GET con fecha
  guardada refleja el presente.

## Hardening previo a producción (2026-07-14)

- El POST delega en `AsistenciaTrabajadorService`.
- La fecha se valida estrictamente como `AAAA-MM-DD`; un valor inválido no cae
  silenciosamente en la fecha actual ni genera registros.
- Solo se aceptan las marcas `0` y `1`, y se valida el lote completo antes de
  escribir.
- Todos los `update_or_create` del lote corren en una única
  `transaction.atomic()`, por lo que una falla intermedia revierte lo anterior.
- `observaciones` ahora es un campo visible y editable en cada fila, en lugar
  de un input oculto.
- La cobertura agrega fecha/marca inválidas, rollback de una segunda escritura
  fallida y render del campo de observaciones existente.
