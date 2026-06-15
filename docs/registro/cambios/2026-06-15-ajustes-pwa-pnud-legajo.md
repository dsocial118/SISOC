# Ajustes PWA, PNUD y legajo de comedor

## Fecha
2026-06-15

## Objetivo
Resolver ajustes funcionales y visuales acumulados sobre PWA mobile, SISOC web y datos de prueba, con foco en programas PNUD, conformidad mensual de prestaciones, actividades, nomina, colaboradores, legajo de comedor y notificaciones.

## Alcance
- Datos locales de prueba para organizaciones, comedores y usuario PWA.
- PWA mobile: pantallas de espacios, prestaciones conveniadas, actividades, colaboradores, beneficiarios, mensajes y notificaciones.
- SISOC web: legajo de comedor, nomina, colaboradores y alertas de conformidad.
- Backend PWA/SISOC: reglas de conformidad, actividades, nomina PWA, datos sociales e indocumentados.

## Archivos tocados
- `comedores/api_serializers.py`
- `comedores/api_views.py`
- `comedores/forms/comedor_form.py`
- `comedores/services/colaborador_espacio_service/impl.py`
- `comedores/templates/comedor/comedor_detail.html`
- `comedores/templates/comedor/nomina_form.html`
- `comedores/utils.py`
- `comedores/views/colaborador.py`
- `comedores/views/comedor.py`
- `comedores/views/nomina.py`
- `pwa/admin.py`
- `pwa/api_serializers.py`
- `pwa/api_views.py`
- `pwa/migrations/0019_actividad_responsable_vigencia.py`
- `pwa/models.py`
- `pwa/services/actividades_service.py`
- `pwa/services/nomina_service.py`
- `mobile/src/api/activitiesApi.ts`
- `mobile/src/api/prestacionesApi.ts`
- `mobile/src/api/spacesApi.ts`
- `mobile/src/features/home/CollaboratorsCard.tsx`
- `mobile/src/features/home/OrganizationHomePage.tsx`
- `mobile/src/features/home/SpaceActivitiesPage.tsx`
- `mobile/src/features/home/SpaceActivityDetailPage.tsx`
- `mobile/src/features/home/SpaceCollaboratorFormPage.tsx`
- `mobile/src/features/home/SpaceDetailPage.tsx`
- `mobile/src/features/home/SpaceHubPage.tsx`
- `mobile/src/features/home/SpaceMessageDetailPage.tsx`
- `mobile/src/features/home/SpaceNominaPersonFormPage.tsx`
- `mobile/src/features/home/SpacePrestacionesConveniadasPage.tsx`
- `mobile/src/features/home/useUnreadMessages.ts`
- `mobile/src/index.css`
- `mobile/src/ui/AppLayout.tsx`

## Cambios realizados
- Se corrigieron migraciones y columnas faltantes en la base local de prueba para levantar Django.
- Se crearon datos demo locales: 6 organizaciones, 10 comedores con programas Alimentar/PNUD y usuario PWA `pwa3`.
- Se ajustaron scrollbars y layout mobile de `/app-org`, incluyendo separadores y titulos de Organizaciones/Espacios.
- Se ajusto Prestaciones conveniadas mobile: botones Si/No, encabezado comun, modo oscuro, selector de periodo y alertas pendientes.
- Se amplio conformidad mensual de prestaciones: disponible todo el mes, seleccion de mes vencido, una conformidad por mes, soporte Abordaje Comunitario y ventana de 6 meses segun convenio.
- Se agregaron alertas de conformidad pendiente en PWA y legajo SISOC.
- Se oculto alta/modulo de colaboradores para Abordaje Comunitario - Linea Secos y se bloqueo la edicion web de colaboradores dados de baja.
- Se agregaron responsable y vigencia en meses a actividades PWA.
- Se reemplazo la eliminacion de actividades PWA por inactivacion, conservando actividad e historial de personas asociadas.
- Se oculto Referentes del Espacio en informacion institucional mobile para Alimentar Comunidad.
- Se quito el dato/badge Judicializado del legajo para todos los programas.
- Se corrigieron selects en modo oscuro para genero y prestaciones conveniadas.
- Se separo la edicion de datos sociales de beneficiarios de la validacion/sync de actividades.
- Se hizo opcional la fecha de nacimiento para personas indocumentadas.
- Se habilito en alta web de nomina PNUD elegir Prestacion alimentaria y/o Actividades, permitiendo altas solo con actividades.
- Se reemplazo Relevamientos por Actividades en legajo de comedores PNUD, mostrando actividades PWA del espacio y detalles complementarios.
- Se corrigio la lectura de mensajes mobile abiertos desde push para marcar backend y actualizar el badge global de notificaciones.

## Supuestos
- La deteccion de PNUD se basa en `is_pnud_comedor`.
- Para conformidad, cuando existe convenio con fecha de inicio se respetan los 6 meses de vigencia; si no hay periodo de convenio cargado se mantiene la logica segura disponible.
- Las actividades mostradas en el legajo PNUD se toman desde `ActividadEspacioPWA`.
- Los datos demo y ajustes directos de base corresponden al entorno local de prueba.

## Validaciones ejecutadas
- `docker compose exec django python manage.py check`: OK, sin issues.
- `npm run build` en `mobile`: OK.
- `git diff --check` en repo principal: OK.
- `git diff --check` en `mobile`: OK, con advertencias de normalizacion LF/CRLF.

## Pendientes / riesgos
- El build mobile informa warning de chunk mayor a 500 kB; no bloquea el build.
- Los datos demo y saneamientos de base local no son cambios versionados.
- Queda recomendada prueba manual de flujos principales: conformidad mensual, alta PNUD solo actividades, legajo PNUD, notificaciones push y lectura de mensajes.
