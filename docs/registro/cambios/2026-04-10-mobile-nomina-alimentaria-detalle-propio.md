# Mobile Nómina alimentaria: detalle propio sin actividades

## Cambio

Se agregó una pantalla de detalle específica para la `Nómina alimentaria` de espacios con programa `Alimentar Comunidad`.

## Reglas aplicadas

- La lista de `Nómina alimentaria` ya no navega al detalle general de nómina.
- El detalle específico no muestra:
  - prestaciones de actividades
  - contador de actividades
  - bloque de actividades vinculadas
  - acción para sumar a actividad
- Se conserva el resto del flujo relevante para Alimentar Comunidad:
  - datos personales
  - asistencia mensual
  - historial de asistencias
  - baja de la persona

## Alcance

- Pantallas afectadas:
  - `mobile/src/features/home/SpaceNominaAlimentariaPage.tsx`
  - `mobile/src/features/home/SpaceNominaAlimentariaPersonDetailPage.tsx`
  - `mobile/src/app/router.tsx`
- No se modificó el detalle general de nómina usado por otros programas.
