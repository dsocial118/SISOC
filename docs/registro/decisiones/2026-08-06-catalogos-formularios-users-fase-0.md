# Catálogos de formularios de Users en Fase 0

## Contexto

`users.forms` importaba modelos de Comedores, Duplas y Organizaciones solamente
para construir los querysets de campos administrativos. Esas dependencias
directas mantenían abiertas tres excepciones del ratchet de importaciones.

## Decisión

Se incorporó `users.form_catalogs` como puerto de querysets para formularios.
Cada dominio registra durante el arranque el proveedor de su propio queryset:

- Organizaciones para el selector PWA de organizaciones.
- Comedores para el selector PWA de comedores.
- Duplas para la asignación de duplas coordinadas.

Los formularios consultan el puerto al inicializarse. El campo de duplas usa un
queryset vacío en la definición de clase y recibe el queryset de dominio en
`__init__`, evitando consultar el registro antes de que Django ejecute los
`AppConfig.ready()`.

## Consecuencias

- Se conservan los widgets, ordenamientos y reglas de validación de los
  formularios existentes.
- `users.forms` ya no conoce modelos de los tres dominios aportantes.
- Un proveedor ausente falla de forma explícita, en lugar de devolver un
  queryset silenciosamente incompleto.
- El ratchet reduce tres excepciones de importaciones de Users.

## Validación

- `black --check` sobre los archivos modificados.
- `pytest tests/test_user_form_catalogs_port_unit.py tests/test_users_pwa_forms.py tests/test_users_auth_flows.py -q`.
- `python manage.py check`.
- `lint-imports`.
