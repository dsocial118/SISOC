# Resolución de accesos PWA de importaciones en Fase 0

## Contexto

El importador de usuarios PWA validaba modelos de Organizaciones y Comedores,
expandía las organizaciones a sus comedores y detectaba el programa Alimentar
Comunidad desde `users.services_user_import`. Esto mantenía las dos últimas
excepciones runtime de Users en el ratchet y mezclaba reglas de Comedores con
la orquestación de creación de usuarios.

## Decisión

Se creó el puerto `users.pwa_import_access`. Comedores registra en su
`AppConfig.ready()` un resolvedor que:

- conserva la validación de IDs y sus mensajes de error;
- devuelve los IDs seleccionados y los comedores expandidos por organización;
- identifica el primer comedor Alimentar Comunidad para calcular permisos
  delegables.

Users conserva la construcción de `AccesoComedorPWA`, la autorización y la
creación o actualización de usuarios. No recibe instancias de modelos de
Comedores u Organizaciones.

## Consecuencias

- Se mantienen las asociaciones por organización y por espacio individual.
- Una organización sin comedores continúa rechazándose antes de modificar al
  usuario, incluso si ya tenía accesos activos.
- El puerto falla explícitamente si Comedores no se registró durante el
  arranque de Django.
- Se eliminan las dos excepciones runtime restantes de Users; el baseline de
  Fase 0 queda sólo con los dos casos de tooling de `core`.

## Validación

- `black --check` sobre los archivos modificados.
- `pytest tests/test_pwa_import_access_port_unit.py tests/test_users_regressions.py -q`.
- `python manage.py check`.
- `lint-imports`.
