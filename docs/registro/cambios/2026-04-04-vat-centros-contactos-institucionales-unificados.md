# VAT - centros con contactos institucionales unificados

Fecha: 2026-04-04

## Qué cambió

- La pantalla de alta y edición de centros VAT deja de mostrar la sección visual `4. Autoridades`.
- La carga de responsables y contactos institucionales se concentra en `3.2 Contactos de la institución`.
- Cada fila institucional ahora contempla `Nombre y apellido del responsable`, `Rol / Área`, `Documento`, `Teléfono` y `Correo electrónico`.
- Los campos de `3.2 Contactos de la institución` dejaron de ser obligatorios en el alta/edición del centro.
- El primer contacto cargado se normaliza como principal y sincroniza los campos legacy de `Centro` para mantener compatibilidad con vistas y procesos existentes.

## Alcance

- Se agregó migración para `InstitucionContacto.documento`.
- El flujo de alta/edición de centros dejó de crear o actualizar `AutoridadInstitucional` desde ese formulario.
- Se elimina el modelo `AutoridadInstitucional` y sus rutas, vistas, admin y API, migrando sus datos útiles hacia `InstitucionContacto`.

## Validación prevista

- Tests puntuales del alta y edición de centros VAT.
- Verificación manual de que `/vat/centros/nuevo/` y `/vat/centros/<id>/editar/` muestran una sola tabla institucional.