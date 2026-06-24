# Ajustes PWA mobile, permisos y nomina mensual

## Fecha
2026-06-23

## Objetivo
Consolidar ajustes funcionales de PWA/mobile y flujos relacionados para permisos granulares, prestaciones mensuales, capacitaciones, nomina, subusuarios, documentos y celiaquia, manteniendo el acceso de prestaciones mensuales fuera del menu principal de la PWA.

## Alcance
Se incluyeron cambios en la experiencia mobile, APIs PWA, permisos de escritura, generacion documental de nomina alimentaria mensual, legajo de comedor, subusuarios PWA y flag de celiaquia en nomina. Tambien se revisaron flujos AJAX de documentos en admisiones y organizaciones.

## Archivos tocados
- `admisiones/`
- `organizaciones/`
- `comedores/`
- `pwa/`
- `users/`
- `mobile/src/api/`
- `mobile/src/app/router.tsx`
- `mobile/src/auth/permissionCodes.ts`
- `mobile/src/features/home/`
- `docs/tmp/WORKLOG.md`

## Cambios realizados
- Se ajusto el cambio de estado AJAX en documentos de admisiones para re-renderizar la fila completa con permisos server-side y corregir la deteccion de grupo tecnico/abogado.
- Se reviso el flujo de documentos de organizaciones; ya reemplaza la fila completa con el partial backend despues de subir o cambiar estado.
- Se agregaron permisos separados para prestaciones mensuales, nomina, colaboradores y gestion de usuarios PWA, aplicados a acciones de escritura y rutas directas cuando corresponde.
- Se elimino la card directa de prestaciones mensuales del hub principal de PWA mobile y se mantuvo el acceso desde Informacion Institucional.
- Se ajustaron consumidores mobile de capacitaciones para usar `results`, exponer metadata y mostrar enlace a Formando Capital Humano.
- Se mantuvieron certificados heredados desde intervenciones en capacitaciones.
- Se agrego generacion versionada de PDF de nomina destinatarios al guardar asistencia alimentaria mensual, con URL en la respuesta API y exposicion en documentos/legajo del comedor.
- Se muestran los ultimos PDFs de nomina mensual PWA como filas documentales en intervenciones del legajo de comedor.
- Se agrego gestion de subusuarios PWA desde mobile con trazabilidad de creador, asignacion a espacios del representante y permisos limitados al alcance del usuario creador.
- Se agrego el flag `persona_con_celiaquia` en perfil de nomina PWA, API/mobile, badge en nomina del comedor y dato en legajo ciudadano.

## Supuestos
- El acceso a prestaciones mensuales debe conservar la funcionalidad, pero no mostrarse como card directa en el menu principal de la PWA durante esta etapa.
- Los permisos nuevos separan visibilidad/consulta de acciones de escritura cuando el flujo lo permite.
- La documentacion se genero desde `docs/tmp/WORKLOG.md`; no se agrego contexto no registrado alli salvo rutas generales de modulos afectados.

## Validaciones ejecutadas
- `npm run build` en `mobile` paso correctamente despues de corregir la ubicacion de `canManagePrestaciones` fuera del ternario de `cardStyle`.
- Se verifico con busqueda local que `Prestaciones conveniadas` no queda referenciado en `SpaceHubPage.tsx` y permanece accesible desde `SpaceDetailPage.tsx`.
- Se verifico `git status --short` en repo raiz y `mobile` antes de generar documentacion.

## Pendientes / riesgos
- El repo raiz estaba en `Issues-y-cambios-varios-0626` detras de `origin/Issues-y-cambios-varios-0626` por 1 commit al momento de cierre; no se hizo pull para evitar mezclar cambios de cierre con sincronizacion de historial.
- No se ejecutaron validaciones Django completas en Docker desde esta tarea de cierre; el cierre documenta cambios acumulados del WORKLOG y valida el ajuste mobile revisado en la sesion.
