# VAT/INET: selección múltiple para aceptar/rechazar inscriptos en lote (#2132)

## Contexto y alcance

La pestaña **Inscriptos** del detalle de comisión de curso listaba las
inscripciones con una única acción por fila: "Borrar". Con comisiones de 55
inscriptos, procesarlas una por una es impracticable.

**Aclaración de alcance.** El ticket dice que "la aceptación o rechazo se realiza
de a uno por vez", pero eso hoy existe en la pestaña **Lista de espera**
(Admitir / Rechazar), no en Inscriptos. El mockup, la flecha y "al lado del botón
Agregar inscripto" apuntan sin ambigüedad al toolbar de **Inscriptos**, y los
criterios de aceptación dicen "tabla de inscriptos" tres veces. Se implementó en
**Inscriptos**.

Lista de espera **no** se tocó. El endpoint es reutilizable, así que extenderlo
ahí es sólo markup si se pide.

## Cambio

### Service (`VAT/services/inscripcion_service.py`)

`InscripcionService.actualizar_estado_en_lote(inscripciones, nuevo_estado, usuario)`
→ `{"actualizadas": [...], "sin_cambios": [...], "errores": [(insc, msg)]}`.

Delega cada fila en `actualizar_estado_inscripcion` para no duplicar reglas de
transición (cupo, voucher, lista de espera).

**Sin transacción envolvente, a propósito.** Cada inscripción se procesa en la
transacción de `actualizar_estado_inscripcion`. Un fallo puntual —cupo completo,
voucher sin saldo— no descarta los cambios ya aplicados: en una acción sobre un
listado se quiere aplicar lo que se pueda e informar qué quedó afuera y por qué,
no perder 54 aceptaciones porque la 55 no tenía cupo.

### View / URL (`VAT/views/curso.py`, `VAT/urls.py`)

`InscripcionCursoCambiarEstadoLoteView` en
`vat/cursos/comisiones/<pk>/inscripciones/cambiar-estado-lote/`, gateada con
`VAT.change_inscripcion` (el mismo permiso del cambio de estado individual).

- **Whitelist de estados**: sólo `inscripta` y `rechazada`. El endpoint individual
  acepta cualquier estado válido del modelo; para el lote se restringe para que un
  POST armado a mano no mueva N inscripciones a cualquier estado por esta vía.
- **Scope doble**: la comisión se resuelve por `_scoped_comisiones_curso_queryset`
  y las inscripciones se filtran por `comision_curso=comision` **además** del id,
  así un id de otra comisión no entra al lote (hay test).
- Devuelve messages separados: éxitos, "ya estaban en ese estado" y un error por
  fila fallida con el motivo.

### Template (`vat/oferta_institucional/comision_detail.html`)

- Checkbox por fila + checkbox de selección total en el `<thead>`.
- Botones **Aceptar** / **Rechazar** junto a "Agregar inscripto", con contador de
  seleccionados y `disabled` cuando no hay selección.
- Modal de confirmación que anticipa cuántas filas cambian realmente y cuántas ya
  estaban en ese estado.
- CSS nuevo: `.ci-lote-acciones`, `.ci-lote-conteo`, `.ci-tbl-col-check`,
  `.sisoc-btn:disabled`.

Los checkbox viven en la tabla, fuera del `<form>`; al confirmar, el JS copia los
seleccionados como `<input type="hidden" name="inscripciones">`. Así se evita
envolver la tabla en un form (donde ya hay enlaces de borrado y de detalle).

## Columna "Estado" agregada (fuera de los criterios)

La tabla de inscriptos mostraba Apellido, Nombre, Documento, Email, Teléfono y
Asistencia — **sin el estado de la inscripción**. Pero el listado incluye todo
menos `en_espera`: `pre_inscripta`, `inscripta`, `validada_presencial`,
`completada`, `rechazada` y `abandonada` conviven ahí.

Sin esa columna el operador seleccionaría a ciegas, sin saber a quién está
aceptando ni si ya estaba aceptado. Se agregó una columna Estado con pill de
color. No estaba en los criterios de aceptación, pero la feature es inusable sin
ella.

## Riesgos de voucher (preexistentes, amplificados por el lote)

Verificado: **no existe ningún camino de reintegro de voucher** en
`VoucherService` (`recargar_voucher` es la recarga mensual; `cancelar_voucher`
cancela el voucher entero).

1. **Rechazar no reintegra.** `pre_inscripta` e `inscripta` están ambos en
   `ESTADOS_INSCRIPCION_OCUPAN_CUPO`, y `crear_inscripcion` debita el voucher
   cuando el estado ocupa cupo. Rechazar libera el cupo pero **no devuelve el
   crédito**. El lote convierte 1 crédito perdido en N.
2. **Aceptar una fila ya `rechazada` re-debita.** `rechazada` no ocupa cupo, así
   que la transición a `inscripta` cumple `pasa_a_ocupar_cupo and not
   ocupaba_cupo` y **debita de nuevo** un crédito que nunca se devolvió: doble
   cobro.

Ambos son del flujo de a uno y quedan fuera del alcance de este ticket. Lo que se
hizo para acotarlos:

- La columna Estado hace visible qué filas están `rechazada` antes de aceptarlas.
- El modal de confirmación informa cuántas filas cambian de estado realmente.
- Los errores por fila se reportan en pantalla en vez de fallar en silencio.

**Recomendación**: abrir un ticket de reintegro de voucher antes de que este lote
se use sobre comisiones con `usa_voucher=True`.

## Decisiones de UX

**"Seleccionar todos" respeta el filtro de búsqueda.** Aplica a las filas que
pasan el buscador (todas las páginas, no sólo la visible). Con un filtro activo,
marcar todos y afectar las 55 de la comisión sería una sorpresa fea.

**Cambiar el filtro limpia la selección.** Evita aplicar una acción en lote sobre
filas que el operador dejó de ver.

**El redirect vuelve a `#inscriptos`**, aprovechando el soporte de hash en el
controlador de solapas agregado en `2026-07-27-vat-comision-resultados-acta.md`.

## Validación

- 12 tests nuevos en `VAT/tests.py`: aceptar en lote, rechazar en lote, sólo
  afecta lo seleccionado, sin selección no hace nada, estado fuera del whitelist,
  aislamiento entre comisiones, reporte de "ya estaban en ese estado", éxitos
  parciales con error de cupo reportado, gate de permiso, scope territorial (404),
  y dos del service (resumen y estado inválido).
- Los tests de gate usan `resolve()` + `RequestFactory` en lugar del test client,
  y los mensajes se leen con `get_messages(response.wsgi_request)` sin seguir el
  redirect: así **los 12 corren en el venv local** pese al problema de
  Python 3.14 documentado en `2026-07-27-vat-comision-resultados-acta.md`.
- El render del panel se validó aparte con `RequestFactory` (checkbox por fila,
  select-all, ambos botones deshabilitados, modal, pills de estado).
- Suite VAT completa: 68F/163P antes → 68F/175P después. **Cero regresiones.**
- `black` y `manage.py check` limpios. `pylint`: 9.93/10 en
  `inscripcion_service.py` (subió desde 9.87 de baseline; las 4 advertencias que
  quedan son preexistentes de `prevalidar_inscripcion` y `crear_inscripcion`).
- `djlint`: el markup agregado no introduce violaciones nuevas.
