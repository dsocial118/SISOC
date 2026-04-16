# Mobile/Web: Capacitaciones, Relevamiento, Notificaciones e Iconos

## Fecha
2026-04-11

## Objetivo
Implementar y estabilizar el flujo de capacitaciones para espacios del programa Alimentar Comunidad en mobile y web, junto con ajustes de UX en nómina/relevamiento/notificaciones, y correcciones de errores de runtime/timeouts.

## Alcance
- Mobile PWA:
  - HUB, Información institucional, Relevamiento, Capacitaciones y Notificaciones.
  - Carga/borrado de fotos de espacio.
  - Contadores y badges de notificaciones.
  - Actualización de íconos PWA (manifest, favicon, service worker).
- Backend Django/DRF:
  - Modelo, servicios y endpoints para certificados de capacitaciones.
  - Reglas de negocio para re-subida, rechazo/aceptación y borrado.
  - Ajustes de robustez en `/api/users/me/`.
- Web Django templates:
  - Card y tabla de capacitaciones en detalle de comedor.
  - Flujo AJAX de validación/rechazo con observación inline.

## Archivos tocados
- `mobile/src/features/home/SpaceHubPage.tsx`
- `mobile/src/features/home/SpaceDetailPage.tsx`
- `mobile/src/features/home/SpaceRelevamientoDetailPage.tsx`
- `mobile/src/features/home/SpaceCapacitacionesPage.tsx`
- `mobile/src/features/home/OrganizationNotificationsPage.tsx`
- `mobile/src/features/home/useUnreadMessages.ts`
- `mobile/src/features/home/SpaceNominaAlimentariaPage.tsx`
- `mobile/src/features/home/SpaceNominaAlimentariaAttendancePage.tsx`
- `mobile/src/api/spacesApi.ts`
- `mobile/src/api/capacitacionesApi.ts`
- `mobile/src/app/router.tsx`
- `mobile/index.html`
- `mobile/vite.config.ts`
- `mobile/src/sw.ts`
- `comedores/models.py`
- `comedores/migrations/0036_capacitacion_comedor_certificado.py`
- `comedores/services/capacitaciones_certificados_service.py`
- `comedores/api_views.py`
- `comedores/api_serializers.py`
- `comedores/views/capacitaciones.py`
- `comedores/views/comedor.py`
- `comedores/views/__init__.py`
- `comedores/urls.py`
- `comedores/templates/comedor/comedor_detail.html`
- `pwa/api_views.py`
- `pwa/services/nomina_service.py`
- `users/api_views.py`

## Cambios realizados
- Se agregó soporte completo de certificados de capacitaciones:
  - Nuevo modelo `CapacitacionComedorCertificado` con 8 capacitaciones fijas y estados.
  - Servicios para inicialización, carga, revisión, borrado y serialización.
  - Endpoints mobile para listar, subir y eliminar certificados.
  - Restricción funcional a programa **Alimentar Comunidad** en web y mobile.
- Se agregó card/flujo de capacitaciones:
  - Mobile: card en Información y módulo en HUB, pantalla dedicada, preview de archivo, estados en pills y acciones de subir/borrar.
  - Web: card final en detalle de comedor con tabla y acciones AJAX.
- Se ajustó rechazo en web:
  - Rechazo con editor inline debajo de la fila (textarea + aceptar/cancelar), sin prompt.
  - Placeholder final: `Ingrese una observacion`.
- Se corrigieron errores y performance:
  - Fix runtime en HUB por ícono no definido.
  - Timeouts en mobile (`capacitaciones`, `relevamiento`, `información`) mediante reducción de refresh forzado y timeout extendido en `getSpaceDetail`.
  - Fallback defensivo en `/api/users/me/` para evitar 500 en bootstrap de sesión.
- Se mejoró UX mobile:
  - Card completa clickeable en Relevamiento/Capacitaciones.
  - Contador de fotos ajustado a fotos visibles en mobile (tope 3).
  - Vacío de notificaciones simplificado (`No hay notificaciones.`), centrado.
  - Badge de notificaciones de Organización ahora incluye también certificados rechazados.
  - Actualización de íconos app/PWA a `sisoc_ico_192.png` y `sisoc_ico_512.png`.
- Ajustes en nómina alimentaria:
  - Botón Asistencia reubicado.
  - Buscador con acción limpiar.
  - Checkbox maestro para selección masiva.
  - Indicadores visuales de asistencia por persona.

## Supuestos
- Los certificados rechazados deben considerarse notificaciones pendientes para el badge general de Organización.
- La regla de negocio de certificados aplica solo a espacios cuyo programa sea exactamente “Alimentar Comunidad”.
- Cuando existe certificado cargado para una capacitación, no corresponde habilitar re-subida directa sin eliminación previa.

## Validaciones ejecutadas
- `mobile`: `npm run build` (OK).
- `backend`: intento de `docker compose exec django python manage.py check` sin éxito por permisos locales de Docker (`permission denied` sobre `docker_engine`).
- `git status`: no ejecutable en entorno actual por `dubious ownership` del repositorio.

## Pendientes / riesgos
- Completar `manage.py check` y pruebas backend en un entorno con permisos Docker habilitados.
- Agregar tests automatizados de regresión para:
  - Rechazo/aceptación/borrado de certificados.
  - Conteo de notificaciones con certificados rechazados.
  - Flujos de timeout/reintento en pantallas mobile.
