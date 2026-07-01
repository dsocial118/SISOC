# 2026-06-25 - VPSL: permiso para ver itinerarios globales

## Cambio

- Se agrega el permiso `ver_para_ser_libre.view_all_itinerarios_vpsl`.
- El permiso permite ver todos los itinerarios VPSL sin aplicar la restriccion por provincia asignada.
- El listado de itinerarios permite filtrar por provincia cuando el usuario tiene este permiso.

## Motivo

Habilitar un perfil de coordinacion general que pueda consultar y comprobar itinerarios creados en cualquier provincia, sin requerir que el usuario tenga una provincia territorial asignada.

## Alcance

- No modifica el flujo de creacion de itinerarios: la creacion sigue requiriendo usuario provincial con provincia asignada.
- No reemplaza permisos de edicion, aprobacion, eliminacion o exportacion. Esos permisos siguen controlandose por sus permisos Django existentes.
