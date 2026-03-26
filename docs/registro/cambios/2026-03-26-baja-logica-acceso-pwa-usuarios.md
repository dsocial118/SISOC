# 2026-03-26 - Baja lógica e historial de acceso PWA en usuarios

## Problema

Al editar un usuario y desmarcar `Habilitar acceso a SISOC - Mobile`, el formulario podía devolver:

- `Marque este campo para configurar el acceso mobile.`

Esto ocurría porque seguían entrando en validación valores residuales de organizaciones/espacios aunque el checkbox principal ya estuviera desactivado.

## Cambio aplicado

- El formulario ahora ignora `tipo_asociacion_pwa`, `organizaciones_pwa` y `comedores_pwa` cuando `es_representante_pwa=False`.
- Quitar el acceso mobile en edición ya no genera error y aplica la baja lógica correctamente.
- El acceso PWA no se borra físicamente:
  - la fila `AccesoComedorPWA` queda persistida;
  - `activo=False`;
  - se completa `fecha_baja`.
- Se agregó auditoría explícita en `AuditAccesoComedorPWA` para registrar:
  - `create`
  - `reactivate`
  - `deactivate`

## Archivos principales

- `users/forms.py`
- `users/models.py`
- `users/services_pwa.py`
- `users/migrations/0019_accesocomedorpwa_fecha_baja_and_audit.py`
- `tests/test_users_pwa_forms.py`

## Validación

- `docker-compose exec django pytest tests/test_users_pwa_forms.py`

## Nota operativa

- Para que esto funcione en base, hay que aplicar la migración `users.0019`.
