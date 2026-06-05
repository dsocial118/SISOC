# Ajustes PWA y web de comedores PNUD

## Fecha
2026-06-05

## Objetivo
Actualizar flujos mobile y web vinculados a comedores PNUD, nominas, actividades, colaboradores y notificaciones, corrigiendo problemas de UI y comportamiento reportados durante la sesion.

## Alcance
- PWA mobile: catalogo y seleccion de actividades, restricciones PNUD, loading/skeleton, pantalla de rendicion en Android, colaboradores y notificaciones.
- Web: nomina de comedores con tabs Alimentaria/Actividades/Todas, dashboard superior, badges sociales y ABM de Actividades PNUD.
- Configuracion: permisos, bootstrap y migraciones para gestionar actividades PNUD activas/inactivas.

## Archivos tocados
- `comedores/forms/actividades_pnud_form.py`
- `comedores/services/colaborador_espacio_service/impl.py`
- `comedores/services/comedor_service/impl.py`
- `comedores/templates/comedor/actividades_pnud_confirm_deactivate.html`
- `comedores/templates/comedor/actividades_pnud_form.html`
- `comedores/templates/comedor/actividades_pnud_list.html`
- `comedores/templates/comedor/nomina_detail.html`
- `comedores/urls.py`
- `comedores/views/__init__.py`
- `comedores/views/actividades_pnud.py`
- `comedores/views/nomina.py`
- `core/constants.py`
- `pwa/api_views.py`
- `pwa/catalogo_seed.py`
- `pwa/migrations/0017_sync_catalogo_actividades_pwa.py`
- `pwa/migrations/0018_catalogoactividadpwa_manage_permission.py`
- `pwa/models.py`
- `static/custom/css/nominaDetail.css`
- `templates/includes/sidebar/new_opciones.html`
- `templates/includes/sidebar/opciones.html`
- `users/bootstrap/groups_seed.py`
- `users/migrations/0033_bootstrap_actividades_pnud_groups.py`
- `mobile/src/app/router.tsx`
- `mobile/src/features/home/CollaboratorsCard.tsx`
- `mobile/src/features/home/OrganizationNotificationsPage.tsx`
- `mobile/src/features/home/RendicionContextPage.tsx`
- `mobile/src/features/home/SpaceActivitiesPage.tsx`
- `mobile/src/features/home/SpaceCollaboratorFormPage.tsx`
- `mobile/src/features/home/SpaceHubPage.tsx`
- `mobile/src/features/home/collaboratorsOffline.ts`
- `mobile/src/sync/engine.ts`
- `mobile/src/ui/AppLayout.tsx`
- `mobile/src/ui/AppLoadingSpinner.tsx`

## Cambios realizados
- Se actualizo el catalogo de actividades disponible en PWA y se limito su disponibilidad/precarga a comedores PNUD.
- Se agrego ABM web de Actividades PNUD con permisos de visualizacion/gestion, estado Activo/Inactivo, baja logica, filtros por estado, buscador y selector de categoria existente/nueva.
- Se ajusto la nomina web para alternar entre Alimentaria, Actividades y Todas, con metricas dinamicas y badges para comunidad indigena o situacion de calle.
- Se reemplazo el dashboard superior de nomina por tarjetas agrupadas y se retiro el bloque redundante de estadisticas detalladas.
- Se corrigio overflow horizontal en Android en la pantalla mobile de rendicion.
- Se ajusto el skeleton/loading mobile para evitar recorte del spinner.
- Se redisenaron los selectores mobile de categoria/actividad, reemplazando pildoras por listas seleccionables consistentes.
- Se separo el flujo de colaboradores mobile en paginas dedicadas para alta, edicion y reactivacion.
- Se bloqueo la edicion de colaboradores dados de baja, se agrego reactivacion controlada y boton de baja en edicion.
- Se hizo optimista la baja desde listado de colaboradores para ocultar editar mientras queda pendiente.
- Se hizo idempotente la baja de colaboradores ante remoto inexistente o ya inactivo.
- Se corrigio la baja con fecha de alta futura usando una fecha valida y manteniendo el DELETE 5xx como pendiente.
- Se agruparon las notificaciones generales mobile una sola vez aunque el usuario tenga varios comedores relacionados.

## Supuestos
- Las actividades PWA de este modulo aplican solo a comedores PNUD.
- Las actividades creadas manualmente desde el ABM no deben ser desactivadas por el bootstrap del catalogo.
- La baja de colaboradores es logica y la fecha de baja no debe ser anterior a la fecha de alta.
- Un mensaje general representa un unico comunicado para el usuario, aunque sea visible desde varios comedores.

## Pendientes / riesgos
- Revisar manualmente en dispositivos Android los ajustes visuales de PWA sobre loading, rendicion y selectores.
- Revisar manualmente el ABM de Actividades PNUD con usuarios con permiso de solo lectura y con permiso de gestion.
