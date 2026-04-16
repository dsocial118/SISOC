# Mobile Nómina alimentaria: asistencia masiva por período

## Cambio

Se reemplazó la toma individual de asistencia para `Nómina alimentaria` por un flujo masivo desde el listado.

## Reglas aplicadas

- En `Nómina alimentaria` se agrega un botón `Asistencia` debajo del buscador.
- Ese botón abre una pantalla específica con toda la nómina alimentaria del espacio.
- Cada fila muestra:
  - apellido
  - nombre
  - DNI
  - check individual precargado según la asistencia ya tomada en el período actual
- La pantalla incluye acciones `Seleccionar todo` y `Deseleccionar todo`.
- `Guardar asistencia` sincroniza exactamente la selección contra el período mensual actual.
- La asistencia sigue siendo única por período.
- El detalle individual de `Nómina alimentaria` deja de permitir toma manual para no duplicar caminos.

## Alcance

- Backend:
  - `pwa/services/nomina_service.py`
  - `pwa/api_views.py`
  - `pwa/api_urls.py`
  - `pwa/api_serializers.py`
  - `tests/test_pwa_nomina_api.py`
- Mobile:
  - `mobile/src/api/nominaApi.ts`
  - `mobile/src/features/home/SpaceNominaAlimentariaPage.tsx`
  - `mobile/src/features/home/SpaceNominaAlimentariaAttendancePage.tsx`
  - `mobile/src/features/home/SpaceNominaAlimentariaPersonDetailPage.tsx`
  - `mobile/src/app/router.tsx`
