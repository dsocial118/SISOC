# Mobile nómina: formulario separado y botón flotante

## Fecha
- 2026-03-29

## Alcance
- Separación del alta y edición de personas de nómina en pantallas dedicadas.
- Reemplazo del botón superior de alta por un botón flotante circular con `+`.

## Cambios
- Se creó `mobile/src/features/home/SpaceNominaPersonFormPage.tsx` como pantalla dedicada para:
  - alta de persona en nómina;
  - edición de prestaciones y actividades de una persona existente;
  - validación RENAPER en el alta cuando corresponde.
- Se simplificó `mobile/src/features/home/SpaceNominaPage.tsx` para que quede como listado liviano con:
  - tablero resumen;
  - tabs;
  - buscador;
  - listado de personas;
  - botón flotante fijo abajo a la derecha.
- Se actualizó `mobile/src/features/home/SpaceNominaPersonDetailPage.tsx` para agregar acceso a edición.
- Se agregaron rutas nuevas en `mobile/src/app/router.tsx`:
  - `/app-org/espacios/:spaceId/nomina/nueva`
  - `/app-org/espacios/:spaceId/nomina/:nominaId/editar`

## Resultado esperado
- La lista de nómina queda más limpia y enfocada en navegación.
- El alta de persona se dispara desde un FAB verde ubicado en la parte inferior derecha.
- La edición ya no comparte espacio con el listado y se resuelve desde el detalle de cada persona.
- En las pantallas de alta y edición se usa la flecha de volver del header en lugar del botón de sincronizar.
- El formulario ya no muestra botón `Cancelar`; la sincronización se dispara al guardar.
