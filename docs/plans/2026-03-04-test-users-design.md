# Diseño: usuarios de testing adicionales

## Objetivo
Extender el comando `users/management/commands/create_test_users.py` para que, en entornos con `DEBUG=True`, se creen usuarios QA por rol y nuevos superadmins, y documentar el listado de usuarios de prueba.

## Alcance
- Agregar creación automática de usuarios QA por cada persona (Juan, Agustina, Facundo, Camilo) y roles (legales, abogado, tec), con contraseña `"1"`.
- Crear usuarios `asampaulo`, `fsuarez`, `jalfonso`, `cparra` como superadmins con contraseña `"1"`.
- Agregar nuevos roles QA: `coordinador`, `operador`, `auditor`.
- Documentar los usuarios en `docs/usuarios_test.md`.

## Decisiones de diseño
- Reutilizar exactamente los grupos actuales de `legalesqa`, `abogadoqa` y `tecnicoqa` para los roles `legales`, `abogado`, `tec`.
- Generar los usernames en minúsculas concatenando nombre y rol (ej: `facundotec`, `juanabogado`).
- Email: `"{username}@example.com"`.
- Superadmins sin grupos adicionales.

### Roles nuevos propuestos
Basado en uso de grupos en `core/constants.py` y `comedores/urls.py`:
- **coordinador**: permisos amplios de comedores/acompañamiento y grupo de rol.
  - Grupos: `Coordinador Equipo Tecnico`, `Comedores`, `Comedores Listar`, `Comedores Ver`, `Comedores Editar`, `Comedores Relevamiento Ver`, `Comedores Relevamiento Detalle`, `Comedores Observaciones Crear`, `Comedores Observaciones Detalle`, `Comedores Observaciones Editar`, `Comedores Observaciones Eliminar`, `Comedores Intervencion Ver`, `Comedores Intervencion Crear`, `Comedores Intervencion Editar`, `Comedores Intervenciones Detalle`, `Comedores Nomina Ver`, `Acompanamiento Listar`, `Acompanamiento Detalle`.
- **operador**: operador general con permisos de operación sin borrado.
  - Grupos: `Comedores`, `Comedores Listar`, `Comedores Ver`, `Comedores Relevamiento Ver`, `Comedores Relevamiento Detalle`, `Comedores Observaciones Crear`, `Comedores Observaciones Detalle`, `Comedores Observaciones Editar`, `Comedores Intervencion Ver`, `Comedores Intervencion Crear`, `Comedores Intervencion Editar`, `Comedores Intervenciones Detalle`, `Comedores Nomina Ver`, `Acompanamiento Listar`, `Acompanamiento Detalle`.
- **auditor**: acceso solo lectura.
  - Grupos: `Comedores`, `Comedores Listar`, `Comedores Ver`, `Comedores Relevamiento Ver`, `Comedores Relevamiento Detalle`, `Comedores Observaciones Detalle`, `Comedores Intervencion Ver`, `Comedores Intervenciones Detalle`, `Comedores Nomina Ver`, `Acompanamiento Listar`, `Acompanamiento Detalle`.

## Flujo y datos
- El comando agrega usuarios si no existen, o actualiza email/clave si ya existen.
- Se agregan grupos con `Group.objects.get_or_create`.

## Manejo de errores
- Mantener el comportamiento actual del comando (sin manejo adicional).

## Testing
- No se agrega test automático por tratarse de un comando de management; se valida manualmente en desarrollo si fuera necesario.

## Supuestos
- El rol `Coordinador Equipo Tecnico` es el coordinador operativo principal (no se usa `Coordinador general`).
- Los grupos mencionados existen o son creados previamente por `create_groups`.
