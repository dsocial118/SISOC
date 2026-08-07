# Issue 2188: capacitaciones y actividades PNUD

## Objetivo

Corregir las regresiones informadas luego del PR: acceso denegado a Capacitaciones desde Informacion Institucional y conteo duplicado de actividades con varios dias u horarios.

## Cambios

- Capacitaciones queda disponible para cualquier usuario PWA con acceso activo al espacio, sin limitarse al rol representante ni al programa Alimentar Comunidad.
- Los endpoints PWA de capacitaciones admiten a cualquier usuario con acceso activo al espacio.
- La tarjeta del legajo SISOC cuenta actividades activas distintas por catalogo; los dias y horarios siguen visibles como filas independientes en el detalle.

## Validacion

- Tests unitarios de permisos y agrupacion del contador.
