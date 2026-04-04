## Contexto

Se ajustaron hallazgos puntuales reportados por CI en `centrodeinfancia` para destrabar el job de `pylint`, sin cambiar comportamiento funcional.

## Cambios

- En `centrodeinfancia/forms_formulario_cdi.py` se redujo la complejidad ciclomática de `FormularioCDIForm.clean()` agrupando reglas de limpieza en tuplas de configuración y loops acotados.
- En `centrodeinfancia/formulario_cdi_schema.py` se partió una línea larga dentro de las opciones de `fuente_agua_segura_consumo`.
- En `centrodeinfancia/models.py` se dejó una supresión local de `too-many-lines`, consistente con el rol actual del módulo como agregado de dominio amplio.

## Validación

- `black --diff --check centrodeinfancia/forms_formulario_cdi.py --config pyproject.toml`
- `black --diff --check centrodeinfancia/formulario_cdi_schema.py --config pyproject.toml`
- `black --diff --check centrodeinfancia/models.py --config pyproject.toml`

## Observaciones

- No pude ejecutar `pylint` localmente en Windows porque la instalación local de `pylint_django` falla al cargar el plugin (`NoSuchChecker` en `TypeChecker`). La referencia operativa para este ajuste sigue siendo el log de CI provisto.
