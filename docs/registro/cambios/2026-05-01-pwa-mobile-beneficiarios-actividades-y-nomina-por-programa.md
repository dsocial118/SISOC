# Cierre de mejoras PWA móvil y reglas de nómina por programa

## Fecha
2026-05-01

## Objetivo
Mejorar la usabilidad y consistencia de la PWA móvil (beneficiarios, actividades, navegación, estados de carga/errores, acentos), y alinear backend PWA de nómina con la lógica de programas (PNUD directo vs flujo con admisión) para evitar desfasajes entre Web y Mobile.

## Alcance
- Refactor UI/UX de módulos móviles de Beneficiarios y Actividades.
- Nueva navegación y detalle de actividades con gestión de inscriptos.
- Robustecimiento de carga/cache/refresh para conexión lenta.
- Correcciones de acentos/mojibake y múltiples fixes de sintaxis TS/TSX.
- Ajuste backend de creación de nómina PWA según `usa_admision_para_nomina`.
- Validación técnica con tests backend y build frontend.

## Archivos tocados
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
- `pwa/services/nomina_service.py`
- `pwa/tests.py`

## Cambios realizados
- Se unificó el lenguaje visible de “Nómina” a “Beneficiarios” en pantallas móviles relevantes.
- Se rediseñó la experiencia de Beneficiarios (botones superiores, resúmenes de asistentes/edades y detalle de persona).
- Se movió “Cargar actividad” a ruta dedicada `/actividades/nueva` y se creó detalle `/actividades/:activityId`.
- En detalle de actividad se agregó edición, eliminación y gestión de inscriptos:
  - baja individual con botón `Quitar` en cada inscripto,
  - alta múltiple desde nómina con checks + `Guardar selección`.
- Se ajustó la pantalla de alta de actividad para ocultar agenda/filtros y mostrar “Horarios ya creados” al seleccionar actividad.
- Se mejoró robustez ante conexión lenta (reintentos, cache fallback, pull-to-refresh in-place y aviso de datos cacheados).
- Se estandarizó la presentación visual de errores en tarjetas rojas semitransparentes con texto blanco.
- Se corrigieron múltiples errores de sintaxis/compilación causados por operadores ternarios truncados y mojibake.
- Backend PWA: `create_nomina_persona` ahora respeta programa del comedor:
  - programas con admisión: vínculo por admisión,
  - PNUD / programas sin admisión: nómina directa por comedor.

## Supuestos
- La rama de trabajo activa es `SiSOC-Mobile-29-04` y no se cambia de rama para este cierre.
- El estado actual del repositorio puede contener cambios previos no vinculados estrictamente a este cierre.

## Validaciones ejecutadas
- `docker compose exec django pytest pwa/tests.py -q` ? `3 passed`.
- `npm run build` en `mobile/` ? build OK (con warning de chunk grande, sin error bloqueante).
- Se agregaron tests de regresión para la decisión de vínculo de nómina por programa en `pwa/tests.py`.

## Pendientes / riesgos
- Existe warning de tamaño de bundle en build de mobile (`chunk > 500kB`), no bloqueante pero conviene optimizar en una tarea separada.
- Persisten cambios históricos en el working tree fuera del foco de este cierre; revisar alcance al momento de preparar PR final.
