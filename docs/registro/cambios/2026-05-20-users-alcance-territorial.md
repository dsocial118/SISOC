# Users - alcance territorial provincial

## Contexto

Hasta este cambio, `users.Profile.provincia` era el único dato territorial de un usuario provincial. Ese modelo no permitía expresar alcances parciales como provincia + municipio o provincia + municipio + localidad, y podía inducir a tratar una provincia padre como alcance completo aunque solo fuera parte de un scope más específico.

## Decisión

La regla nueva vive en `users.ProfileTerritorialScope`, asociado a `Profile`, con:

- `provincia` obligatoria.
- `municipio` opcional.
- `localidad` opcional.
- `scope_key` interno para evitar duplicados equivalentes.
- validación jerárquica de provincia, municipio y localidad.

`Profile.provincia` se conserva solo como compatibilidad temporal. La migración crea un scope provincia-only para cada perfil provincial legacy que tenía provincia asignada.

## Reglas operativas

- Un usuario provincial sin scopes no obtiene acceso global.
- Un scope provincia-only habilita la provincia completa.
- Un scope provincia + municipio no habilita la provincia completa.
- Un scope provincia + municipio + localidad no habilita otras localidades del municipio.
- Municipio y localidad deben pertenecer a los padres seleccionados.
- Las vistas y servicios deben consumir `users.territorial_scope` en lugar de leer autorización desde `profile.provincia`.

## Superficies actualizadas

- Alta y edición de usuarios: campo JSON oculto con filas dinámicas de alcances.
- API de contexto de usuario: se mantiene `provincia_id` y se agrega `territorial_scopes`.
- VAT, CDI y Celiaquía: filtros principales migrados al servicio central.
- Celiaquía evalúa los scopes subprovinciales contra la geografía del ciudadano del legajo.
