# PWA mobile subusuarios y permisos delegados

## Fecha
2026-06-24

## Objetivo
Permitir que un usuario principal de SISOC Mobile creado desde SiSoc Web pueda crear subusuarios desde la PWA, asignarles espacios y permisos delegados, y mantener trazabilidad de esas operaciones.

## Alcance
- Usuarios principales PWA creados/editados desde SiSoc Web.
- Subusuarios PWA creados desde la app mobile.
- Permisos delegables por comedor/espacio.
- Vista web de edición de usuarios principales y subusuarios.
- Auditoría de alta, baja y edición de permisos de accesos PWA.

## Archivos tocados
- `comedores/api_views.py`
- `pwa/api_views.py`
- `pwa/migrations/0024_backfill_representantes_pwa_permissions.py`
- `users/admin.py`
- `users/api_permissions.py`
- `users/api_serializers.py`
- `users/forms.py`
- `users/models.py`
- `users/migrations/0038_auditaccesocomedorpwa_update_permissions_choice.py`
- `users/services_pwa.py`
- `users/templates/user/user_form.html`
- `users/views.py`
- `mobile/src/api/authApi.ts`
- `mobile/src/api/spaceUsersApi.ts`
- `mobile/src/features/home/SpaceUsersPage.tsx`

## Cambios realizados
- Los usuarios principales PWA de SiSoc Web reciben siempre los permisos operativos mobile de colaboradores, subusuarios, nómina y prestaciones mensuales.
- El permiso de rendiciones mobile queda separado y editable desde el tilde histórico de SiSoc Web.
- Se agregó backfill para otorgar solo los permisos operativos nuevos a representantes PWA existentes, sin modificar rendiciones mobile.
- Los operadores/subusuarios PWA pueden acceder al flujo mobile de espacios y operar según permisos delegados.
- Se agregó endpoint para editar permisos de un subusuario creado por el usuario principal, sin permitir delegar `pwa.manage_usuarios_pwa`.
- El backend permite acceso por comedor a usuarios PWA activos y exige permisos específicos para acciones de escritura.
- La PWA mobile permite crear subusuarios con espacios y permisos, y editar permisos de subusuarios creados por el usuario principal.
- La edición web del usuario principal muestra los subusuarios mobile creados por él.
- La edición web de un subusuario mobile muestra su estado, espacios y permisos en modo informativo, sin confundirlo con un usuario principal PWA.
- Los permisos mobile se muestran en Web con nombres legibles, no con códigos internos.
- Se agregó auditoría para edición de permisos de subusuarios con permisos anteriores y nuevos en metadata.
- `AuditAccesoComedorPWA` quedó visible en el admin de Django como consulta de solo lectura.

## Supuestos
- El usuario principal PWA es el representante creado/editado desde SiSoc Web.
- Los subusuarios PWA son operadores creados desde la app mobile.
- Un subusuario solo puede recibir espacios dentro del alcance del usuario principal.
- Un subusuario solo puede recibir permisos delegables que el usuario principal ya tenga, excluyendo la creación/gestión de subusuarios.
- No se puede reconstruir desde la base local qué representantes tenían rendiciones mobile antes de una migración ya aplicada; cualquier corrección puntual debe hacerse desde el checkbox web.

## Validaciones ejecutadas
- `powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 validate`
  - `black --check`: OK.
  - `djlint --check`: OK.
  - smoke tests: 588 passed, 2375 deselected, 3 warnings de logout GET de Django.
  - migraciones: `No changes detected`.
- `npm run build` en `mobile/`: OK.

## Pendientes / riesgos
- El build mobile conserva una advertencia de Vite por chunk mayor a 500 kB.
- Si una base local ya recibió rendiciones mobile por una migración previa, no se puede reconstruir automáticamente quién tenía ese permiso originalmente; corregir casos puntuales desde el checkbox web.
