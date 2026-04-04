## 2026-03-29 - Actividades mobile con duración

### Contexto

Se alineó el módulo de Actividades de SISOC Mobile con el alcance funcional vigente, incorporando el dato faltante de duración y completando el detalle de inscriptos.

### Cambios

- Se agregó `duracion_actividad` al modelo `ActividadEspacioPWA`.
- La API PWA de actividades ahora expone y valida `duracion_actividad` en alta, edición y listado.
- En mobile, el formulario de actividades solicita:
  - categoría
  - actividad
  - día
  - horario
  - duración
- El detalle visual de cada actividad muestra la duración configurada.
- El listado de inscriptos dentro del detalle de actividad ahora incluye también la fecha de nacimiento.

### Supuestos

- Se mantuvo el flujo actual que permite cargar múltiples combinaciones de día y horario para una misma actividad desde un único formulario.
- `duracion_actividad` se modeló como texto corto para permitir formatos operativos del equipo, por ejemplo `60 minutos` o `1 hora 30 min`.
