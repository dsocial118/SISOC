# Mobile nómina alimentaria: toast y redirección al guardar asistencia

## Cambio

- Al guardar asistencia masiva sin error, la app vuelve a `Nómina alimentaria` del espacio y muestra un toast verde de confirmación.
- Si el guardado falla, la pantalla de asistencia permanece abierta y muestra un toast rojo con el mensaje de error.
- Al dar de alta una persona en `Nómina alimentaria`, la app vuelve al listado y muestra un toast verde, en lugar de navegar al detalle individual.
- La pantalla de asistencia reemplaza el texto de personas ya registradas por una barra de progreso `registradas / total`.

## Alcance

- `mobile/src/features/home/SpaceNominaAlimentariaAttendancePage.tsx`
- `mobile/src/features/home/SpaceNominaAlimentariaPage.tsx`
- `mobile/src/ui/AppToast.tsx`
