# Centro de Infancia: nómina, asistencia y datos RENAPER

## Alcance

Este documento consolida los contratos actualmente implementados para la
asistencia sobre nómina y la precarga RENAPER en el alta de trabajadores de
Centro de Infancia (CDI). No reemplaza la guía de roles y pruebas funcionales
de SIMEPI/CDI.

## Asistencia sobre nómina

- La asistencia diaria usa `NominaCentroInfancia`, no `Trabajador`.
- Solo se muestran nóminas activas. Una nómina dada de baja se conserva para
  editar la asistencia de la fecha en que ya tiene un registro; una nómina
  pendiente no es elegible.
- Para cada fila, `presente=1` registra presencia, `presente=0` ausencia y la
  ausencia de marca elimina el registro de asistencia existente para esa fecha.
- La escritura valida las marcas recibidas, bloquea las nóminas y las
  asistencias involucradas, y se ejecuta en una única transacción.
- El calendario devuelve los días que tienen al menos una asistencia, sin
  distinguir presencia de ausencia ni exigir carga completa.
- La URL histórica de asistencia de trabajadores redirige a la asistencia de
  nómina, preservando los parámetros de consulta.

Las rutas de asistencia requieren `centrodeinfancia.change_centrodeinfancia`
y aplican el scope central del CDI. Ese scope delimita EGP por territorio,
referentes por `AccesoCDI` activo, trabajadores por `Trabajador.usuario` y los
roles nacionales por alcance nacional. El rol Auditoría no puede mutar CDI,
trabajadores, nóminas ni formularios.

## Precarga y bloqueo RENAPER de trabajadores

- La búsqueda consulta RENAPER solo cuando no encuentra ciudadanos locales,
  el texto de búsqueda es numérico y tiene al menos siete dígitos.
- Los campos con valor provenientes de RENAPER se incluyen en un token firmado
  con el CDI y el usuario que inició el alta. El token vence a los 15 minutos.
- Al persistir, solo se aceptan valores que provengan de ese token. Se guardan
  los nombres de esos campos en `Trabajador.campos_verificados_renaper`.
- Esos campos se muestran deshabilitados tanto durante el alta como en la
  edición. Django conserva el valor inicial o de instancia, por lo que un POST
  no puede sobrescribirlo.
- No hay una excepción implementada para corregir un dato verificado por
  RENAPER; habilitarla requiere una decisión y una funcionalidad nueva.

## Rutas y permisos

| Flujo | Ruta | Permiso |
| --- | --- | --- |
| Asistencia de nómina | `/centrodeinfancia/<pk>/nomina/asistencia/` | `change_centrodeinfancia` |
| Calendario de asistencia | `/centrodeinfancia/<pk>/nomina/asistencia/calendario/` | `change_centrodeinfancia` |
| Edición de trabajador | `/centrodeinfancia/<pk>/trabajadores/<trabajador_id>/editar/` | `change_trabajador` |

## Referencias de implementación y validación

- `centrodeinfancia/services.py`: `AsistenciaNominaCentroInfanciaService`.
- `centrodeinfancia/views.py`: `AsistenciaNominaCentroView`, calendario y
  `TrabajadorCentroInfanciaCreateView`.
- `centrodeinfancia/urls.py`: protección de rutas y redirección histórica.
- `centrodeinfancia/tests/test_asistencia_nomina.py` y
  `centrodeinfancia/tests/test_trabajadores_views.py`: regresión de asistencia
  y flujo de trabajador.
- `docs/registro/cambios/2026-07-16-cdi-validaciones-trabajador.md`:
  validaciones, migraciones y contrato RENAPER.
- `docs/registro/cambios/2026-07-17-cdi-asistencia-nomina.md`: reglas de
  negocio y compatibilidad de asistencia.
- `docs/registro/cambios/2026-07-15-cdi-enforcement-alcances.md`: alcance por
  rol y restricción de Auditoría.
- `docs/qa/2038-roles-simepi-cdi-guia-testeo.md`: guía funcional de roles.
