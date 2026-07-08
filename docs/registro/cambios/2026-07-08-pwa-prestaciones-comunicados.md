# Ajustes PWA de prestaciones y comunicados

## Fecha
2026-07-08

## Objetivo
Resolver los comentarios de los issues 1972, 1974 y 1978 sobre prestaciones conveniadas en PWA/legajo y comunicados dirigidos a organizaciones.

## Alcance
- Prestaciones alimentarias de admisiones con Informe Tecnico Complementario validado.
- Prestaciones PNUD/Abordaje expuestas en PWA desde datos de convenio.
- Comunicados a organizaciones en PWA, con visibilidad y agrupacion separadas de los comunicados a espacios.

## Archivos tocados
- `acompanamientos/acompanamiento_service.py`
- `comedores/api_views.py`
- `comedores/services/comedor_service/impl.py`
- `comunicados/api_views.py`
- `pwa/api_serializers.py`
- `pwa/api_views.py`
- `pwa/services/mensajes_service.py`
- `pwa/view_helpers.py`
- `tests/test_pwa_comedores_api.py`
- `tests/test_pwa_mensajes_api.py`
- `mobile/src/api/messagesApi.ts`
- `mobile/src/features/home/OrganizationMessagesPage.tsx`
- `mobile/src/features/home/OrganizationNotificationsPage.tsx`
- `mobile/src/features/home/SpaceMessagesPage.tsx`
- `mobile/src/features/home/useUnreadMessages.ts`

## Cambios realizados
- Se centralizo la seleccion del informe tecnico efectivo para priorizar un Informe Tecnico Complementario validado sobre el informe base finalizado.
- La PWA de prestaciones usa `ComedorDatosConvenioPnud` para comedores PNUD/Abordaje y registra conformidad sin `InformeTecnico`.
- Los comunicados a organizaciones solo se exponen a usuarios con acceso PWA de tipo organizacion.
- Los comunicados a organizaciones se serializan como `seccion: organizacion`, con contadores y seccion propia en la respuesta PWA.
- La app mobile muestra y agrupa comunicaciones a organizaciones separadas de comunicaciones a espacios, evitando duplicados por comedor.
- El endpoint legado de comunicados por comedor dejo de incluir comunicados dirigidos a organizaciones.
- Se agregaron tests cercanos para prestaciones PNUD y visibilidad/lectura de comunicados de organizacion.

## Supuestos
- Para PNUD/Abordaje, la fuente de prestaciones conveniadas es `ComedorDatosConvenioPnud` cuando `usa_datos_convenio_pnud(comedor)` aplica.
- Un usuario relacionado a una organizacion se identifica por `AccesoComedorPWA.tipo_asociacion = organizacion` y `organizacion_id` coincidente.
- `mobile/` es un repositorio Git anidado y sus cambios se validan y versionan desde su propio estado.

## Validaciones ejecutadas
- `docker compose exec django pytest tests/test_pwa_comedores_api.py::test_prestacion_alimentaria_expone_fecha_finalizacion_desde_historial tests/test_pwa_comedores_api.py::test_prestacion_alimentaria_pnud_expone_datos_convenio tests/test_pwa_mensajes_api.py::test_list_mensajes_por_espacio_no_expone_organizacion_a_usuario_de_espacio tests/test_pwa_mensajes_api.py::test_list_mensajes_por_espacio_expone_organizacion_solo_a_usuario_organizacion` - 4 passed.
- `npm run build` en `mobile/` - exitoso. Vite informo warning no bloqueante por chunks mayores a 500 kB.

## Pendientes / riesgos
- No se ejecuto la suite completa.
- Los cambios de `mobile/` quedan en el repositorio Git anidado y deben incluirse desde ese contexto si se prepara commit separado.
