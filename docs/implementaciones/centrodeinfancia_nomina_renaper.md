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

## Integridad de la nómina vigente

Una persona puede tener, como máximo, una ficha de nómina **vigente** entre
todos los CDI. Para esta regla, vigente significa estado `Activo` o `Pendiente`.
Las fichas en `Baja` y las dadas de baja lógicamente no bloquean un alta ni una
derivación posterior.

- El alta, la reactivación por edición, el Django admin y la restauración desde
  la papelera aplican la misma regla y devuelven un mensaje neutro. No exponen
  el CDI en el que existe la ficha que provoca el conflicto.
- La derivación conserva el histórico: primero deja el origen en `Baja` y crea
  el destino en `Pendiente`, dentro de la misma transacción. También rechaza el
  flujo si la persona tiene una ficha vigente en un **tercer** CDI.
- Antes de persistir una operación que puede crear o reactivar vigencia, el
  servicio bloquea la fila de la persona y revalida bajo lock. Esto serializa
  intentos concurrentes desde CDI diferentes y evita que dos altas simultáneas
  dejen fichas vigentes.

La garantía es de aplicación sobre MySQL/InnoDB; no hay una constraint parcial
en base de datos porque MySQL no la implementa para este caso y los duplicados
históricos no se corrigen automáticamente. Antes de desplegar un cambio de
esta regla conviene revisar los duplicados vigentes existentes, ya que no se
modifican pero pueden bloquear derivaciones posteriores.

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
- `centrodeinfancia/services.py`: validación y serialización de nómina vigente
  por persona (`tiene_nomina_cdi_vigente_en_otro_centro`).
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
- `docs/registro/cambios/2026-08-07-cdi-nomina-vigente-en-un-solo-centro.md`:
  alcance, concurrencia, límites y rollback de la exclusividad de vigencia.
- `docs/qa/2038-roles-simepi-cdi-guia-testeo.md`: guía funcional de roles.
