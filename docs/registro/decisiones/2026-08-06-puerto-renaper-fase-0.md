# 2026-08-06 - Puerto RENAPER para Fase 0

## Contexto

`core.api_views` y la importacion masiva de `ciudadanos` dependian directamente
del cliente RENAPER ubicado en Centro de Familia. La Fase 0 requiere eliminar
esa direccion de dependencia sin adelantar la reubicacion del cliente tecnico,
que es el alcance de la Fase 2.

## Decision

`core.services.renaper` expone un puerto de consulta. Centro de Familia registra
durante su arranque la implementacion existente `consultar_datos_renaper`.
El registro es idempotente para el mismo proveedor y rechaza reemplazos
silenciosos.

## Consecuencias

- `core` y `ciudadanos` dejan de importar Centro de Familia para RENAPER.
- El cliente, cache, clasificacion de errores y respuesta del proveedor actual
  permanecen sin cambios.
- Se retiran dos excepciones runtime de `.importlinter`.
- La Fase 2 puede mover el cliente tecnico a una capa compartida sin cambiar
  consumidores del puerto.

## Validacion

- `pytest tests/test_core_renaper_api_unit.py tests/test_ciudadanos_importacion_masiva.py tests/test_consulta_renaper_unit.py -q`.
- `lint-imports`.
- `python manage.py check` dentro del contenedor Django.
