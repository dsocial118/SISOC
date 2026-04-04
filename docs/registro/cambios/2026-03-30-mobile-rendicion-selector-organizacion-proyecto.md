# Mobile rendición: selector previo por organización y proyecto

Fecha: 2026-03-30

## Qué cambió

- Se agregó una pantalla previa en SISOC Mobile para que el usuario de organización seleccione:
  - la organización sobre la que va a trabajar;
  - el proyecto dentro de esa organización.
- La opción `Rendición` de la barra inferior ahora abre ese selector y ya no entra directo por un espacio arbitrario.
- Después de elegir contexto, el flujo reutiliza las pantallas existentes de listado, alta y detalle de rendiciones.

## Regla de negocio aplicada

- La rendición mobile se considera dentro del alcance `organización + proyecto`.
- Un mismo `codigo_de_proyecto` en otra organización no comparte rendiciones ni bloquea altas por número/período.
- Para espacios sin `codigo_de_proyecto`, el fallback sigue siendo el espacio puntual representado por el `spaceId`.

## Backend

- `RendicionCuentaMensualService._get_project_queryset(...)` ahora filtra por:
  - `comedor__codigo_de_proyecto`
  - y `comedor__organizacion_id`
  cuando el espacio tiene proyecto informado.

## Validación

- `docker-compose exec django pytest tests/test_pwa_comedores_api.py -k "rendiciones_mobile_scope_por_organizacion_y_proyecto or crear_rendicion_mobile_permite_mismo_proyecto_en_otra_organizacion or rendiciones_list_and_detail_by_scope or crear_rendicion_mobile_con_datos_generales or crear_rendicion_mobile_rechaza_numero_repetido_y_periodo_solapado"`
- `npm run build` en `mobile/`
