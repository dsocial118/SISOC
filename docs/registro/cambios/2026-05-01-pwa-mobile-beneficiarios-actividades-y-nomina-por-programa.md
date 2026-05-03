# Cierre de mejoras PWA móvil y reglas de nómina por programa

## Fecha
2026-05-01

## Objetivo
Mejorar la usabilidad y consistencia de la PWA móvil (beneficiarios, actividades, navegación, estados de carga/errores y acentos), y alinear el backend PWA de nómina con la lógica de programas (PNUD directo vs flujo con admisión) para evitar desfasajes entre Web y Mobile.

## Alcance versionado en este PR
- Ajuste backend de creación de nómina PWA según `usa_admision_para_nomina`.
- Registro de historial de observaciones de nómina PWA.
- Tests de regresión para la decisión de vínculo de nómina por programa.
- Documentación funcional del cierre mobile.

## Referencias operativas fuera del diff versionado
La carpeta `mobile/` está ignorada por git en este repositorio. Los archivos mobile listados abajo documentan el cierre funcional de la rama `SiSOC-Mobile-29-04`, pero no se entregan como archivos versionados dentro de este PR a `main`:
- `mobile/src/features/home/SpaceNominaPage.tsx`
- `mobile/src/features/home/SpaceNominaAlimentariaPage.tsx`
- `mobile/src/features/home/SpaceNominaAlimentariaPersonDetailPage.tsx`
- `mobile/src/features/home/SpaceNominaPersonDetailPage.tsx`
- `mobile/src/features/home/SpaceActivitiesPage.tsx`
- `mobile/src/features/home/SpaceActivityDetailPage.tsx`
- `mobile/src/features/home/OrganizationHomePage.tsx`
- `mobile/src/features/home/OrganizationMessagesPage.tsx`
- `mobile/src/features/home/OrganizationNotificationsPage.tsx`
- `mobile/src/features/home/SpaceDetailPage.tsx`
- `mobile/src/features/home/SpaceHubPage.tsx`
- `mobile/src/features/home/SpaceCapacitacionesPage.tsx`
- `mobile/src/features/home/useUnreadMessages.ts`
- `mobile/src/ui/AppLayout.tsx`
- `mobile/src/ui/FullScreenPageLoader.tsx`
- `mobile/src/ui/SettingsDrawer.tsx`
- `mobile/src/app/router.tsx`
- `mobile/src/api/nominaApi.ts`
- `mobile/src/api/spacesApi.ts`
- `mobile/src/api/capacitacionesApi.ts`
- `mobile/src/pwa/registerPwa.ts`
- `mobile/src/sw.ts`

## Archivos versionados tocados
- `pwa/services/nomina_service.py`
- `pwa/models.py`
- `pwa/api_serializers.py`
- `pwa/api_views.py`
- `pwa/migrations/0015_nominaobservacionpwa.py`
- `pwa/tests.py`

## Cambios realizados
- Se ajustó `create_nomina_persona` para respetar el programa del comedor:
  - programas con admisión: vínculo por admisión,
  - PNUD / programas sin admisión: nómina directa por comedor.
- Se agregó historial de observaciones PWA en `NominaObservacionPWA`.
- Se expone `observaciones_historial` en la API PWA de nómina.
- Se documentó el cierre funcional mobile asociado, aclarando que `mobile/` no forma parte del diff versionado de este PR.

## Supuestos
- La rama funcional mobile usada como fuente fue `SiSOC-Mobile-29-04`.
- El deploy de código mobile se gestiona fuera del diff versionado de este PR porque `mobile/` está ignorado por git en SISOC.

## Validaciones ejecutadas
- `docker compose exec django pytest pwa/tests.py -q`: `3 passed` en la rama funcional original.
- `npm run build` en `mobile/`: build OK en la rama funcional original, con warning de chunk grande no bloqueante.
- En este PR se agregaron tests de regresión para la decisión de vínculo de nómina por programa en `pwa/tests.py`.

## Pendientes / riesgos
- Existe warning de tamaño de bundle en build de mobile (`chunk > 500kB`), no bloqueante pero conviene optimizar en una tarea separada.
- Antes de mergear a `main`, la validación final debe cerrarse con CI/Docker sobre el PR #1660.
