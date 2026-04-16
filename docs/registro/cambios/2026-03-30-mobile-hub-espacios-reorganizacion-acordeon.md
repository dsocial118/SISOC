# Reorganización del hub de espacios mobile

Fecha: 2026-03-30

## Qué cambió

- Se cambió el header del hub de espacios para mostrar:
  - `Bienvenido {nombre}`
  - `Hub de Espacios`
- Se simplificó la parte superior de la pantalla para dejar una sola card de filtros.
- Se movió la búsqueda dentro de esa misma card de filtros.
- Se reorganizó el contenido inferior en una card de `Organizaciones`.
- Dentro de esa card, cada organización ahora se muestra como acordeón con sus espacios adentro.

## Archivos

- `mobile/src/ui/AppLayout.tsx`
- `mobile/src/features/home/OrganizationHomePage.tsx`

## Criterio aplicado

- Se preservó el filtrado actual por programa, organización, proyecto y búsqueda.
- Se mantuvo el autoingreso cuando el usuario tiene un único espacio operativo.
- Si el usuario además tiene espacios directos fuera de una organización, se mantienen visibles al final del bloque como `Espacios directos`.

## Validación

- `npm run build` en `mobile/`
