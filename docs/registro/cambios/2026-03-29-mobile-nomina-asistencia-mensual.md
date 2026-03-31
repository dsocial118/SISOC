# Mobile nómina: asistencia mensual con historial

## Qué cambió

- Se agregó `pwa.RegistroAsistenciaNominaPWA` para persistir la toma de asistencia por persona y por período.
- La periodicidad activa quedó en `mensual`, usando como referencia el primer día del mes.
- Se expuso `POST /api/pwa/espacios/{comedor_id}/nomina/{nomina_id}/registrar-asistencia/`.
- El listado de nómina mobile ahora devuelve:
  - `asistencia_mes_actual`
- `historial_asistencias` queda reservado para carga diferida;
- el historial completo se consulta bajo demanda por persona en `GET /api/pwa/espacios/{comedor_id}/nomina/{nomina_id}/historial-asistencia/`.
- las actividades vinculadas completas también se consultan bajo demanda por persona en `GET /api/pwa/espacios/{comedor_id}/nomina/{nomina_id}/`.
- En la pantalla mobile de nómina cada persona muestra:
  - estado del mes actual
  - botón `Tomar asistencia`
  - historial visible en el desplegable

## Reglas de negocio implementadas

- Solo puede existir un registro por `nomina + periodicidad + periodo_referencia`.
- Si se intenta registrar la asistencia del mismo mes nuevamente, la API responde el mismo registro sin duplicarlo.
- Cada alta de asistencia genera auditoría en `pwa.AuditoriaOperacionPWA` con entidad `nomina_asistencia`.
- El historial completo ya no se incluye en el listado general de nómina para evitar timeouts en espacios grandes.
- Las actividades detalladas tampoco se incluyen en el listado inicial; la lista solo expone `cantidad_actividades`.

## Supuesto aplicado

- Se modeló una única asistencia periódica por persona de nómina, sin distinguir todavía entre prestación alimentaria y actividades.
- Este recorte mantiene flexibilidad para cambiar la periodicidad más adelante sin reusar indebidamente `NominaEspacioPWA`, que hoy solo representa el perfil/alcance de la persona dentro de Mobile.
