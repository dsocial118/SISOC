# Mobile Hub de espacios: fallback de programa y mensaje sin programa

## Cambio

Se ajusto el Hub del espacio para no perder el programa cuando el detalle del comedor no lo devuelve pero el listado de espacios ya lo conoce.

## Reglas aplicadas

- El nombre de programa del hub ahora se resuelve con esta prioridad:
  - `detail.programa.nombre`
  - `programa__nombre` proveniente del listado/cache de espacios
  - `programName` recibido por navegacion
- Si el backend de detalle responde sin programa, el hub conserva el ultimo nombre de programa conocido y no oculta los modulos correspondientes.
- Cuando no hay programa definido, la leyenda se muestra centrada, sin card contenedora, y en dos renglones:
  - `No hay programa definido.`
  - `Comuníquese con un administrador de la aplicación.`

## Alcance

- Pantalla afectada: `mobile/src/features/home/SpaceHubPage.tsx`
- No se cambiaron contratos de API ni reglas de negocio backend.
