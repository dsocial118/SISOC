# Usuario Coordinador PWA

Implementación del issue #2316.

- Se incorpora el rol exclusivo `Coordinador de Equipo Técnico` para nuevas altas PWA. Su alcance se calcula dinámicamente a partir de los comedores asignados a una o más duplas, más comedores adicionales permanentes.
- El coordinador consulta todos los módulos PWA, incluidos rendiciones, actividades, capacitaciones y subusuarios, sin permisos de gestión.
- El backend aplica el modo de solo lectura también ante llamadas directas: bloquea escrituras y el marcado de mensajes como vistos. Push y cambio de contraseña permanecen disponibles.
- La exclusividad se valida también en los servicios de asignación de representantes,
  incluidos los flujos de importación; el coordinador conserva la lectura de
  notificaciones de rendiciones sin adquirir su permiso de gestión.
- No se altera ni migra el rol de coordinador existente de SISOC web (`Profile.es_coordinador`).

La validación automatizada de Django queda pendiente de un entorno con las dependencias del proyecto: la instalación local no tiene `crispy_forms`.
