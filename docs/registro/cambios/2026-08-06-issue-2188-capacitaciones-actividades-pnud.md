# Issue 2188: capacitaciones y actividades PNUD

## Objetivo

Corregir las regresiones informadas luego del PR: acceso denegado a Capacitaciones desde Informacion Institucional y conteo duplicado de actividades con varios dias u horarios.

## Cambios

- Capacitaciones queda disponible para cualquier usuario PWA con acceso activo al espacio, sin limitarse al rol representante ni al programa Alimentar Comunidad.
- La pantalla mobile consulta directamente los certificados para todos los programas.
- La tarjeta del legajo SISOC cuenta actividades activas distintas por catalogo; los dias y horarios siguen visibles como filas independientes en el detalle.

## Validacion

- Tests unitarios de permisos, disponibilidad mobile y agrupacion del contador.
- Build de la aplicacion mobile.

