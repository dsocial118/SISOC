# CDF: toma de asistencia en actividades de Centro de Familia

## Fecha
2026-07-03

## Objetivo
Permitir tomar asistencia a los participantes inscritos de una actividad de
CDF, replicando el flujo de asistencia del módulo VAT
(`AsistenciaSesionView`) adaptado a la estructura de CDF.

## Diseño
VAT registra asistencia por sesión autogenerada (`SesionComision` →
`AsistenciaSesion`). CDF no tiene sesiones: la unidad de asistencia es
**(participante, fecha)**. La planilla se arma por actividad y fecha (hoy por
defecto), solo sobre participantes con estado `inscrito`.

## Cambios
- **Modelo** `AsistenciaActividad` (`centrodefamilia/models.py`): FK a
  `ParticipanteActividad` + `fecha`, `presente`, `registrado_por`, timestamps.
  `unique_together (participante, fecha)`. Migración `0016_asistenciaactividad`.
- **Service** `centrodefamilia/services/asistencia/`
  (`AsistenciaActividadService`): `parse_fecha` (default hoy, rechaza formato
  inválido y fechas futuras), `obtener_planilla`, `registrar`
  (`update_or_create` atómico; lo no marcado se registra como ausente, igual
  que VAT).
- **Acceso** (`centrodefamilia/access.py`): `puede_tomar_asistencia_cdf` —
  referente del centro (FK legacy o `AccesoCDF` activo), rol CDF SSE
  (`auth.role_cdf_sse`) o superusuario.
- **Vista** `AsistenciaActividadView`
  (`centrodefamilia/views/asistencia.py`): GET planilla con métricas
  presentes/ausentes/sin marcar; POST guarda y redirige a la misma fecha.
  403 para usuarios sin vínculo con el centro.
- **URL** `centros/actividades/<pk>/asistencia/`
  (`actividadcentro_asistencia`), mismo esquema de permisos que las demás
  rutas CDF (`centrodefamilia.view_centro`).
- **UI**: template `centros/actividadcentro_asistencia.html` con el estilo
  Bootstrap/cards propio de CDF (no el tema oscuro de VAT): selector de fecha,
  tarjetas de métricas en vivo, radios Presente/Ausente con "marcar todos".
  Botón "Tomar Asistencia" en el detalle de la actividad (visible solo para
  quien puede tomarla).
- **Tests**: `centrodefamilia/tests/test_asistencia_actividad.py` (service +
  vista + permisos, 9 casos).

## Decisiones
- Se copió el comportamiento VAT de registrar como ausente lo no marcado al
  guardar, para mantener paridad funcional entre módulos.
- No se permite tomar asistencia a fechas futuras (validación nueva, VAT no
  la tiene).
