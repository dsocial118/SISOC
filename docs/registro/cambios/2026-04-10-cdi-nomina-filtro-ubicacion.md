# CDI nomina: filtro encadenado de ubicacion

## Fecha
2026-04-10

## Contexto
En la vista de alta de nomina CDI (`NominaCentroInfanciaCreateView`) los campos de domicilio `provincia_domicilio`, `municipio_domicilio` y `localidad_domicilio` no actualizaban sus opciones en cascada al cambiar la seleccion, a diferencia de formularios equivalentes en comedores/ciudadanos.

## Cambio aplicado
- Se inyectaron las URLs AJAX estandar del proyecto (`ajax_load_municipios`, `ajax_load_localidades`).
- Se implemento un cargador AJAX nativo en `centrodeinfancia/templates/centrodeinfancia/nomina_form.html`, sin Select2, para preservar los estilos existentes del formulario.
- El encadenamiento apunta a:
  - `#id_provincia_domicilio`
  - `#id_municipio_domicilio`
  - `#id_localidad_domicilio`
- Se mantuvo precarga al abrir el formulario cuando ya existe provincia seleccionada.

## Validacion
- Se agrego test de regresion en `centrodeinfancia/tests/test_nomina_integridad.py` que verifica que la vista renderiza:
  - script `ubicacionSelects.js`
  - endpoints AJAX esperados
  - selectores de los tres campos encadenados

## Compatibilidad
- Cambio backward-compatible.
- Sin cambios de modelo, migraciones ni contratos de API.
