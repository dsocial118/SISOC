# 2026-08-06 - Capacidad de Comedores para permisos PWA

## Contexto

`users.services_pwa` consultaba directamente el modelo `Comedor` y su
servicio de programas para restringir el permiso de rendición móvil en
Alimentar Comunidad.

## Decision

`users.pwa_comedores` define el puerto de esa capacidad. Comedores resuelve
su modelo y programa, y registra la implementación desde `ComedoresConfig.ready()`.

## Consecuencias

- `users` conserva la regla de permisos PWA sin importar el modelo Comedor.
- Comedores mantiene la propiedad de identificar su programa.
- Un proveedor ausente falla explícitamente; el caso sin comedor conserva el
  resultado `False` previo.
- Se retira una excepción runtime de `.importlinter`.

## Validacion

- `black --check users/pwa_comedores.py comedores/pwa_capabilities.py comedores/apps.py users/services_pwa.py tests/test_pwa_comedores_port_unit.py comedores/test_pwa_capabilities.py`.
- `pytest tests/test_pwa_comedores_port_unit.py comedores/test_pwa_capabilities.py tests/test_users_services_pwa.py -q`.
- `python manage.py check`.
- `lint-imports`.
