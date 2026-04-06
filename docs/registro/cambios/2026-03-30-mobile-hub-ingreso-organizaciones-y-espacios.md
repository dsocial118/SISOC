# Mobile hub de ingreso por organizaciones y espacios

## Fecha
- 2026-03-30

## Alcance
- Ajuste del hub inicial mobile para representantes con asociaciones por organización, por espacio o mixtas.

## Cambios
- Se unificó la lógica de acceso del home mobile para clasificar:
  - organizaciones con sus espacios;
  - espacios directos extra fuera de esas organizaciones;
  - casos de autoingreso directo al espacio.
- El home de organización ahora muestra:
  - secciones agrupadas por organización con sus espacios;
  - una sección separada de `Espacios` cuando el usuario también tiene accesos directos.
- Se corrigió el autoingreso para que también entre directo al hub cuando:
  - el usuario tiene un único espacio asignado;
  - el usuario tiene una sola organización y esa organización contiene un único espacio.
- Se actualizó el layout mobile para reutilizar la misma regla de autoingreso en la navegación inferior y en el botón de inicio.
- Se removió la preselección automática de filtros cuando había una sola organización/programa/proyecto para no ocultar espacios extra en asociaciones mixtas.

## Impacto esperado
- Si el usuario tiene organizaciones, ve el listado de sus organizaciones con sus espacios.
- Si el usuario tiene organizaciones y además espacios directos, ve ambos bloques en el hub.
- Si la organización operativa contiene un único espacio y no hay extras, entra directo al espacio.
- Si el usuario sólo tiene un espacio designado, entra directo al espacio.

## Validación
- `npm run build` en `mobile/`
