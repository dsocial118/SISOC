# 2026-08-06 - Contribuciones de dominio para Ciudadano 360

## Contexto

`CiudadanosDetailView` consultaba directamente implementaciones de Celiaquia,
Centro de Familia, Comedores, PWA y VAT para armar el contexto de Ciudadano 360.
Esto invertia la direccion de dependencia: el modulo de ciudadanos conocia los
modelos de dominios que aportan paneles a la pantalla.

## Decision

`ciudadanos.detail_contributions` define un registro de contribuciones. Cada
dominio registra durante `AppConfig.ready()` una funcion que recibe un ciudadano
y devuelve exclusivamente las claves de contexto que ya consume el template.

El registro es idempotente para la misma funcion y rechaza duplicados distintos.
Si una contribucion no esta registrada, la vista conserva el contexto vacio
equivalente al comportamiento anterior cuando el modulo no estaba disponible.

## Consecuencias

- `ciudadanos.views` deja de importar los modelos de los cinco dominios.
- El template, permisos, consultas y claves de contexto se conservan.
- Se retiran cinco excepciones runtime de `.importlinter`.
- RENAPER sigue siendo un corte independiente de la Fase 0.

## Validacion

- `lint-imports`.
- `pytest tests/test_ciudadanos_views_unit.py tests/test_favorite_filters_unit.py -q`.
- `python manage.py check` dentro del contenedor Django.
