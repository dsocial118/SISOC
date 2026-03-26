# 2026-03-26 - Colaboradores unificados entre web y mobile

## Contexto

La app mobile venía usando un flujo propio de colaboradores del espacio basado en el modelo legacy `pwa.ColaboradorEspacioPWA`, con campos manuales (`nombre`, `apellido`, `email`, `rol_funcion`) y sin compartir la nueva lógica web de alta sobre `Ciudadano + RENAPER + ColaboradorEspacio`.

## Cambio aplicado

- Los endpoints PWA de colaboradores pasan a usar `comedores.ColaboradorEspacio` como fuente de verdad.
- Mobile y web ahora comparten las mismas reglas de negocio para colaboradores:
  - búsqueda previa por DNI en SISOC;
  - consulta a RENAPER cuando el ciudadano no existe localmente;
  - creación/reutilización del `Ciudadano`;
  - alta del colaborador del espacio con género, teléfono, fechas y actividades múltiples.
- Se agregaron endpoints auxiliares PWA para mobile:
  - `POST /api/pwa/espacios/{comedor_id}/colaboradores/preview-dni/`
  - `GET /api/pwa/espacios/{comedor_id}/colaboradores/generos/`
  - `GET /api/pwa/espacios/{comedor_id}/colaboradores/actividades/`
- El listado PWA de colaboradores ahora expone:
  - datos del ciudadano;
  - datos específicos del colaborador del espacio;
  - actividades;
  - estado activo/inactivo por `fecha_baja`.
- La baja desde mobile sigue siendo lógica y preserva historial.
- El almacenamiento offline de mobile fue adaptado al nuevo shape de datos y mantiene el historial local de bajas en vez de eliminar filas.

## Archivos principales

- `pwa/api_views.py`
- `pwa/api_serializers.py`
- `pwa/api_urls.py`
- `mobile/src/api/collaboratorsApi.ts`
- `mobile/src/features/home/CollaboratorsCard.tsx`
- `mobile/src/features/home/collaboratorsOffline.ts`
- `mobile/src/sync/engine.ts`
- `mobile/src/db/database.ts`
- `tests/test_pwa_colaboradores_api.py`

## Validación

- `docker-compose exec django pytest tests/test_pwa_colaboradores_api.py`
- `npm run build` en `mobile/`

## Supuestos

- Se mantuvieron las rutas PWA existentes de colaboradores para no romper navegación mobile.
- El modelo legacy `pwa.ColaboradorEspacioPWA` no se eliminó en esta fase; quedó fuera del flujo activo.
